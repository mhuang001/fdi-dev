# -*- coding: utf-8 -*-
from ..pns.jsonio import getJsonObj
from ..dataset.odict import ODict
from ..dataset.dataset import TableDataset
from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize
from .productpool import ProductPool
from ..utils.common import pathjoin, trbk

import filelock
import sys
import shutil
import pdb
import json
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


class ODEncoder(json.JSONEncoder):
    def default(self, obj):
        if issubclass(obj.__class__, ODict):
            return dict(obj)

        # Let the base class default method raise the TypeError
        d = json.JSONEncoder.default(self, obj)
        return d


def writeJsonwithbackup(fp, data):
    """ write data in JSON after backing up the existing one.
    """
    if op.exists(fp):
        os.rename(fp, fp + '.old')
    # js = json.dumps(data, cls=ODEncoder)
    #logger.debug('Writing %s stat %s' % (fp, str(os.path.exists(fp+'/..'))))
    js = serialize(data)
    with open(fp, mode="w+") as f:
        f.write(js)
    logger.debug('JSON saved to: ' + fp)


def wipeLocal(poolpath):
    """
    does the scheme-specific remove-all
    """
    # logger.debug()
    pp = poolpath
    if pp == '/':
        raise(ValueError('Do not remove root directory.'))

    if not op.exists(pp):
        return
    try:
        shutil.rmtree(pp)
        os.mkdir(pp)
    except Exception as e:
        msg = 'remove-mkdir ' + pp + \
            ' failed. ' + str(e) + trbk(e)
        logger.error(msg)
        raise e


class LocalPool(ProductPool):
    """ the pool will save all products in local computer.
    """

    def __init__(self, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """
        # print(__name__ + str(kwds))
        super(LocalPool, self).__init__(**kwds)
        real_poolpath = self.transformpath(self._poolname)
        if not op.exists(real_poolpath):
            os.makedirs(real_poolpath)

        c, t, u = self.readHK()

        logger.debug('created ' + self.__class__.__name__ + ' ' + self._poolname +
                     ' at ' + real_poolpath + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)

    def readHK(self, hktype=None, serialized=False):
        """
        loads and returns the housekeeping data

        hktype: one of 'classes', 'tags', 'urns' to return. default is None to return alldirs
        serialized: if True return serialized form. Default is false.
        """
        if hktype is None:
            hks = ['classes', 'tags', 'urns']
        else:
            hks = [hktype]
        fp0 = self.transformpath(self._poolname)
        with filelock.FileLock(self.lockpath('w'), timeout=5):
            # if 1:
            hk = {}
            for hkdata in hks:
                fp = pathjoin(fp0, hkdata + '.jsn')
                if op.exists(fp):
                    try:
                        with open(fp, 'r') as f:
                            js = f.read()
                    except Exception as e:
                        msg = 'Error in HK reading ' + fp + str(e) + trbk(e)
                        logging.error(msg)
                        raise Exception(msg)
                    r = js if serialized else deserialize(js)
                else:
                    r = '{}' if serialized else dict()
                hk[hkdata] = r
        logger.debug('HK read from ' + fp0)
        return (hk['classes'], hk['tags'], hk['urns']) if hktype is None else hk[hktype]

    def writeHK(self, fp0):
        """
           save the housekeeping data to disk
        """

        for hkdata in ['classes', 'tags', 'urns']:
            fp = pathjoin(fp0, hkdata + '.jsn')
            writeJsonwithbackup(fp, self.__getattribute__('_' + hkdata))

    def schematicSave(self, resourcetype, index, data, tag=None):
        """
        does the media-specific saving.

        index: int
        """
        fp0 = self.transformpath(self._poolname)
        fp = pathjoin(fp0, quote(resourcetype) + '_' + str(index))
        try:
            writeJsonwithbackup(fp, data)
            self.writeHK(fp0)
            logger.debug('HK written')
        except IOError as e:
            logger.error('Save ' + fp + 'failed. ' + str(e) + trbk(e))
            raise e  # needed for undoing HK changes

    def schematicLoadProduct(self, resourcetype, index, serialized=False):
        """
        does the scheme-specific part of loadProduct.

        se
        """
        indexstr = str(index)
        pp = self.transformpath(self._poolname) + '/' + \
            resourcetype + '_' + indexstr
        try:
            with open(pp, 'r') as f:
                js = f.read()
        except Exception as e:
            msg = 'Load' + pp + 'failed. ' + str(e) + trbk(e)
            logger.error(msg)
            raise e
        return js if serialized else deserialize(js)

    def schematicRemove(self, resourcetype, index):
        """
        does the scheme-specific part of removal.
        """
        fp0 = self.transformpath(self._poolname)
        fp = pathjoin(fp0,  quote(resourcetype) + '_' + str(index))
        try:
            os.unlink(fp)
            self.writeHK(fp0)
        except IOError as e:
            logger.error('Remove ' + fp + 'failed. ' + str(e) + trbk(e))
            raise e  # needed for undoing HK changes

    def schematicWipe(self):
        """
        does the scheme-specific remove-all
        """
        wipeLocal(self.transformpath(self._poolname))

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """

        raise(NotImplementedError())
