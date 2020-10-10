# -*- coding: utf-8 -*-


from ..dataset.deserialize import deserializeClassID
from .localpool import LocalPool
from ..utils.common import pathjoin, trbk


import filelock
import sys
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


class HttpPool(LocalPool):
    """ the pool will save all products in Http server.
    """

    def __init__(self, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """
        # print(__name__ + str(kwds))
        super(HttpPool, self).__init__(**kwds)

    def readHKObj(self, hkobj):
        """
        loads a single object of HK
        """
        fp0 = self.transformpath(self._poolname)
        with filelock.FileLock(self.lockpath('r'), timeout=5):
            fp = pathjoin(fp0, hkobj + '.jsn')
            if op.exists(fp):
                try:
                    with open(fp, 'r') as f:
                        content = f.read()
                    r = deserializeClassID(content)
                except Exception as e:
                    msg = 'Error in HK reading ' + fp + str(e) + trbk(e)
                    logging.error(msg)
                    raise Exception(msg)
            else:
                r = dict()
        return r

    def schematicLoadProduct(self, resourcetype, index):
        """
        does the scheme-specific part of loadProduct.
        """
        indexstr = str(index)
        with filelock.FileLock(self.lockpath('r'), timeout=5):
            poolpath = self.transformpath(self._poolname)
            filepath = poolpath + '/' + quote(resourcetype) + '_' + indexstr
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                p = deserializeClassID(content)
            except Exception as e:
                msg = 'Load ' + filepath + ' failed. ' + str(e) + trbk(e)
                logger.error(msg)
                raise e
        return p
