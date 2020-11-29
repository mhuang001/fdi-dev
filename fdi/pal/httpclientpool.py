# -*- coding: utf-8 -*-
from ..pns.jsonio import getJsonObj
from ..pns.fdi_requests import urn2fdiurl, save_to_server, read_from_server, delete_from_server
from .urn import Urn, makeUrn
from ..dataset.odict import ODict
from ..dataset.dataset import TableDataset
from ..dataset.serializable import serialize
from .productpool import ProductPool
from .poolmanager import PoolManager
from .localpool import wipeLocal
from ..utils.common import pathjoin, trbk

import filelock
import shutil
import os
from functools import lru_cache
from os import path as op
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


def writeJsonwithbackup(fp, data):
    """ write data in JSON after backing up the existing one.
    """
    if op.exists(fp):
        os.rename(fp, fp + '.old')
    js = serialize(data)
    with open(fp, mode="w+") as f:
        f.write(js)


class HttpClientPool(ProductPool):
    """ the pool will save all products on a remote server.
    """

    def __init__(self, poolpath_local=None, **kwds):
        """ Initialize connection to the remote server. creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files on server if not exist.

        poolpath_local: sets where to stotr housekeeping data locally. default is None, using PoolManager.PlacePaths['file']
        """
        # print(__name__ + str(kwds))
        super(HttpClientPool, self).__init__(**kwds)

        self._poolpath_local = PoolManager.PlacePaths['file'] if poolpath_local is None else poolpath_local
        real_poolpath = self.transformpath(self._poolname)
        logger.debug(real_poolpath)
        if not op.exists(real_poolpath):
            # os.mkdir(real_poolpath)
            os.makedirs(real_poolpath)
        c, t, u = self.readHK()

        logger.debug('created ' + self.__class__.__name__ + ' ' + self._poolname +
                     ' at ' + real_poolpath + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)

    def getPollpath_local(self):
        """ returns the path where the client stores local data.
        """
        return self._poolpath_local

    @lru_cache(maxsize=5)
    def transformpath(self, path):
        """ use local poolpath

        """
        base = self._poolpath_local
        if base != '':
            if path[0] == '/':
                path = base + path
            else:
                path = base + '/' + path
        return path

    def readHK(self):
        """
        loads and returns the housekeeping data
        """
        poolname = self._poolname
        logger.debug("READ HK FROM REMOTE===>poolurl: " + poolname)
        hk = {}
        try:
            r, msg = read_from_server(None, self._poolurl, 'housekeeping')
            if r != 'FAILED':
                for hkdata in ['classes', 'tags', 'urns']:
                    hk[hkdata] = r[hkdata]
        except Exception as e:
            msg = 'Read ' + poolname + ' failed. ' + str(e) + trbk(e)
            r = 'FAILED'

        if r == 'FAILED':
            logger.error(msg)
            raise Exception(msg)
        return hk['classes'], hk['tags'], hk['urns']

    def writeHK(self, fp0):
        """
           save the housekeeping data to disk
        """

        for hkdata in ['classes', 'tags', 'urns']:
            fp = pathjoin(fp0, hkdata + '.jsn')
            writeJsonwithbackup(fp, self.__getattribute__('_' + hkdata))

    def schematicSave(self, resourcetype, index, data, tag=None):
        """
        does the media-specific saving to remote server
        save metadata at localpool
        """
        fp0 = self.transformpath(self._poolname)
        fp = pathjoin(fp0, resourcetype + '_' + str(index))

        urnobj = Urn(cls=data.__class__,
                     poolname=self._poolname, index=index)
        urn = urnobj.urn
        try:
            res = save_to_server(data, urn, self._poolurl, tag)
            if res['result'] == 'FAILED':
                # print('Save' + fp + ' to server failed. ' + res['msg'])
                logger.error('Save ' + fp + ' to server failed. ' + res['msg'])
                raise Exception(res['msg'])
            else:
                self.writeHK(fp0)
                logger.debug('Saved to server done, HK written in local done')
            logger.debug('Product written in remote server done')
        except IOError as e:
            logger.error('Save ' + fp + 'failed. ' + str(e) + trbk(e))
            raise e  # needed for undoing HK changes

    def schematicLoadProduct(self, resourcetype, index, serialized=False):
        """
        does the scheme-specific part of loadProduct.
        """
        indexstr = str(index)
        poolname = self._poolname
        urn = makeUrn(self._poolname, resourcetype, indexstr)
        logger.debug("READ PRODUCT FROM REMOTE===> " + urn)
        res, msg = read_from_server(urn, self._poolurl)
        if res == 'FAILED':
            raise NameError('Loading ' + urn + ' failed.  ' + msg)
        return res

    def schematicRemove(self, resourcetype, index):
        """
        does the scheme-specific part of removal.
        """
        fp0 = self.transformpath(self._poolname)
        fp = pathjoin(fp0, resourcetype + '_' + str(index))
        urn = makeUrn(self._poolname, resourcetype, index)
        try:
            res, msg = delete_from_server(urn, self._poolurl)
            if res != 'FAILED':
                # os.unlink(fp)
                self.writeHK(fp0)
                return res
            else:
                logger.error('Remove from server ' + fp +
                             'failed. Caused by: ' + msg)
                raise ValueError(msg)
        except IOError as e:
            logger.error('Remove ' + fp + 'failed. ' + str(e) + trbk(e))
            raise e  # needed for undoing HK changes

    def schematicWipe(self):
        """
        does the scheme-specific remove-all
        """
        # logger.debug()
        pp = self.transformpath(self._poolname)

        res, msg = delete_from_server(None, self._poolurl, 'pool')
        if res == 'FAILED':
            logger.error(msg)
            raise Exception(msg)
        if not op.exists(pp):
            return
        try:
            shutil.rmtree(pp)
            os.mkdir(pp)
        except IOError as e:
            err = 'remove-mkdir ' + pp + \
                ' failed. ' + str(e) + trbk(e)
            logger.error(err)
            raise e

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """
