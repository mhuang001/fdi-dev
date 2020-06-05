# -*- coding: utf-8 -*-
from ..pns.jsonio import getJsonObj
from ..dataset.odict import ODict
from ..dataset.dataset import TableDataset
from ..dataset.serializable import serializeClassID
from .productpool import ProductPool
from ..utils.common import pathjoin, trbk
from .productpool import lockpathbase
import filelock
import sys
import shutil
import pdb
import os
from os import path as op
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
    from urllib.parse import urlparse, quote, unquote
else:
    PY3 = False
    strset = (str, unicode)
    from urlparse import urlparse, quote, unquote


def writeJsonwithbackup(fp, data):
    """ write data in JSON after backing up the existing one.
    """
    if op.exists(fp):
        os.rename(fp, fp + '.old')
    js = serializeClassID(data)
    with open(fp, mode="w+") as f:
        f.write(js)


class LocalPool(ProductPool):
    """ the pool will save all products in local computer.
    """

    def __init__(self, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """
        # print(__name__ + str(kwds))
        super(LocalPool, self).__init__(**kwds)

        logger.debug(self._poolpath)
        if not op.exists(self._poolpath):
            os.mkdir(self._poolpath)
        c, t, u = self.readHK()

        logger.debug('pool ' + self._poolurn + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)

    def readHK(self):
        """
        loads and returns the housekeeping data
        """
        fp0 = (self._poolpath)
        #import pdb
        # pdb.set_trace()
        with filelock.FileLock(self.lockpath(), timeout=5):
            # if 1:
            hk = {}
            for hkdata in ['classes', 'tags', 'urns']:
                fp = pathjoin(fp0, hkdata + '.jsn')
                if op.exists(fp):
                    try:
                        r = getJsonObj(self._scheme + '://' + fp)
                    except Exception as e:
                        msg = 'Error in HK reading ' + fp + str(e) + trbk(e)
                        logging.error(msg)
                        raise Exception(msg)
                else:
                    r = dict()
                hk[hkdata] = r
        logger.debug('LocalPool HK read from ' + self._poolpath)
        return hk['classes'], hk['tags'], hk['urns']

    def writeHK(self, fp0):
        """
           save the housekeeping data to disk
        """

        for hkdata in ['classes', 'tags', 'urns']:
            fp = pathjoin(fp0, hkdata + '.jsn')
            writeJsonwithbackup(fp, self.__getattribute__('_' + hkdata))

    def schematicSave(self, typename, serialnum, data):
        """ 
        does the media-specific saving
        """
        fp0 = self._poolpath
        fp = pathjoin(fp0, quote(typename) + '_' + str(serialnum))
        try:
            writeJsonwithbackup(fp, data)
            self.writeHK(fp0)
            logger.debug('HK written')
        except IOError as e:
            logger.error('Save ' + fp + 'failed. ' + str(e) + trbk(e))
            raise e  # needed for undoing HK changes

    def schematicLoadProduct(self, resourcename, indexstr):
        """
        does the scheme-specific part of loadProduct.
        """

        with filelock.FileLock(self.lockpath(), timeout=5):
            uri = self._poolurn + '/' + quote(resourcename) + '_' + indexstr
            try:
                p = getJsonObj(uri)
            except Exception as e:
                msg = 'Load' + uri + 'failed. ' + str(e) + trbk(e)
                logger.error(msg)
                raise e
        return p

    def schematicRemove(self, typename, serialnum):
        """
        does the scheme-specific part of removal.
        """
        fp0 = (self._poolpath)
        fp = pathjoin(fp0,  quote(typename) + '_' + str(serialnum))
        try:
            os.unlink(fp)
            self.writeHK(fp0)
        except IOError as e:
            logger.error('Remove ' + fp + 'failed. ' + str(e) + trbk(e))
            raise e  # needed for undoing HK changes

    @classmethod
    def wipe(cls, poolpath):
        """
        does the scheme-specific remove-all
        """

        # logger.debug()
        pp = poolpath
        if not op.exists(pp):
            return
        if op.isdir(pp):
            with filelock.FileLock(pathjoin(lockpathbase, poolpath, 'lock'), timeout=5):
                # lock file will be wiped, too. so acquire then release it.
                pass
        try:
            shutil.rmtree(pp)
            os.mkdir(pp)
        except Exception as e:
            msg = 'remove-mkdir ' + pp + \
                ' failed. ' + str(e) + trbk(e)
            logger.error(msg)
            raise e

    def schematicWipe(self):
        """
        does the scheme-specific remove-all
        """
        LocalPool.wipe(self._poolpath)

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """
