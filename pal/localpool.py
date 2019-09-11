# -*- coding: utf-8 -*-
import filelock
import os
from pathlib import Path
import collections
import shutil
from urllib.parse import urlparse

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .urn import Urn
from .productref import ProductRef
from .comparable import Comparable
from .common import getJsonObj
from .productpool import ProductPool

from dataset.serializable import serializeClassID
from dataset.dataset import TableDataset
from dataset.odict import ODict
from pns.common import trbk


class LocalPool(ProductPool):
    """ the pool will save all products in local computer.
    """

    def __init__(self, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate ouse-keeping records
        """
        super().__init__(**kwds)

        p = Path(self._poolpath)
        if not p.exists():
            p.mkdir()
        c, t, u = self.readHK()
        logger.debug('pool ' + self._poolurn + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)

    def readHK(self):
        """
        loads and returns the housekeeping data
        """
        fp0 = Path(self._poolpath)
        with filelock.FileLock(self._poolpath + '/lock'):
            hk = {}
            for hkdata in ['classes', 'tags', 'urns']:
                fp = fp0.joinpath(hkdata + '.jsn')
                if fp.exists():
                    r = getJsonObj(str(fp))
                    if r is None:
                        msg = 'Error in HK reading ' + str(fp)
                        logging.error(msg)
                        raise Exception(msg)
                else:
                    r = ODict()
                hk[hkdata] = r
        logger.debug('LocalPool HK read from ' + self._poolpath)
        return hk['classes'], hk['tags'], hk['urns']

    def writeHK(self, fp0):
        """
           save the housekeeping data
        """

        for hkdata in ['classes', 'tags', 'urn']:
            fp = fp0.joinpath(hkdata + '.jsn')
            if fp.exists():
                fp.rename(str(fp) + '.old')
            with fp.open(mode="w+") as f:
                js = serializeClassID(self.__getattribute__('_' + hkdata))
                f.write(js)

    def schematicSave(self, typename, serialnum, data):
        """ 
        does the media-specific saving
        """
        fp0 = Path(self._poolpath)
        fp = fp0.joinpath(typename + '_' + str(serialnum))
        try:
            if fp.exists():
                fp.rename(str(fp) + '.old')
            with fp.open(mode="w+") as f:
                js = serializeClassID(data)
                f.write(js)

            self.writeHK(fp0)
        except IOError as e:
            logger.debug(str(fp) + str(e) + trbk(e))
            raise e  # needed for undoing HK changes

    def schematicRemove(self, typename, serialnum):
        """
        does the scheme-specific removal.
        """
        fp0 = Path(self._poolpath)
        fp = fp0.joinpath(typename + '_' + str(serialnum))
        try:
            fp.unlink()
            self.writeHK(fp0)
        except IOError as e:
            logger.debug(str(fp) + str(e) + trbk(e))
            raise e  # needed for undoing HK changes

    def schematicWipe(self):
        """
        does the scheme-specific remove-all
        """
        with filelock.FileLock(poolpath + '/lock'):
            pass  # lock file will be wiped, too. so release it.
        try:
            shutil.rmtree(poolpath)
            pp = Path(poolpath)
            pp.mkdir()
        except Exception as e:
            msg = 'remove-mkdir ' + poolpath + ' failed'
            logger.error(msg)
            raise e

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """
