# -*- coding: utf-8 -*-
from ..pns.jsonio import getJsonObj
from ..pns.fdi_requests import *
from .urn import Urn
from ..dataset.odict import ODict
from ..dataset.dataset import TableDataset
from ..dataset.serializable import serializeClassID
from .productpool import ProductPool
from ..utils.common import pathjoin, trbk
from ..pns.pnsconfig import pnsconfig as pc
import filelock
import shutil
import os
from os import path as op
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

basepoolpath = pc['basepoolpath_client']

def writeJsonwithbackup(fp, data):
    """ write data in JSON after backing up the existing one.
    """
    if op.exists(fp):
        os.rename(fp, fp + '.old')
    js = serializeClassID(data)
    with open(fp, mode="w+") as f:
        f.write(js)


class HttpClientPool(ProductPool):
    """ the pool will save all products on a remote server.
    """

    def __init__(self, **kwds):
        """ Initialize connection to the remote server. creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files on server if not exist.
        """
        # print(__name__ + str(kwds))
        super(HttpClientPool, self).__init__(**kwds)

        logger.debug(self._poolpath)

        real_poolpath = self.transformpath(self._poolpath)
        logger.debug(real_poolpath)
        if not op.exists(real_poolpath):
            # os.mkdir(real_poolpath)
            os.makedirs(real_poolpath)
        c, t, u = self.readHK()

        logger.debug('pool ' + self._poolurn + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)

    def readHK(self):
        """
        loads and returns the housekeeping data
        """
        poolurn = self._poolurn
        print("READ HK FROM REMOTE===>poolurl: " + poolurn )
        hk = {}
        try:
            r, msg = read_from_server(poolurn, 'housekeeping')
            if r == 'FAILED':
                raise Exception(msg)
            else:
                for hkdata in ['classes', 'tags', 'urns']:
                    hk[hkdata] = r[hkdata]
        except Exception as e:
            err = 'Error in HK reading from server ' + poolurn
            logging.error(err)
            raise Exception(err)
        return hk['classes'], hk['tags'], hk['urns']

    def writeHK(self, fp0):
        """
           save the housekeeping data to disk
        """

        for hkdata in ['classes', 'tags', 'urns']:
            fp = pathjoin(fp0, hkdata + '.jsn')
            writeJsonwithbackup(fp, self.__getattribute__('_' + hkdata))

    def schematicSave(self, typename, serialnum, data, tag=None):
        """
        does the media-specific saving to remote server
        save metadata at localpool
        """
        fp0 = self.transformpath(self._poolpath)
        fp = pathjoin(fp0, typename + '_' + str(serialnum))

        urnobj = Urn(cls=data.__class__, pool=self._poolurn, index=serialnum)
        urn = urnobj.urn
        try:
            res = save_to_server(data, urn, tag)
            if  res['result'] == 'FAILED':
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

    def schematicLoadProduct(self, resourcename, indexstr, urn):
        """
        does the scheme-specific part of loadProduct.
        """
        poolurn = self._poolurn
        uri = poolurn + '/' +  resourcename + '_' + indexstr
        # print("READ PRODUCT FROM REMOTE===>poolurl: " + poolurn )
        try:
            res, msg = read_from_server(urn)
            if res == 'FAILED':
                # print('Load' + uri + 'failed. ' + res['msg'])
                logger.error('Load ' + uri + ' failed.  ' + msg)
                prod = dict()
            else:
                prod = res
        except Exception as e:
            err = 'Load' + uri + 'failed. ' + str(e) + trbk(e)
            logger.error(err)
            raise e
        return prod

    def schematicRemove(self, typename, serialnum, urn):
        """
        does the scheme-specific part of removal.
        """
        fp0 = self.transformpath(self._poolpath)
        fp = pathjoin(fp0, typename + '_' + str(serialnum))
        try:
            res, msg = delete_from_server(urn)
            if res != 'FAILED':
                # os.unlink(fp)
                self.writeHK(fp0)
                return res
            else:
                logger.error('Remove from server ' + fp + 'failed. Caused by: ' + msg)
                raise msg
        except IOError as e:
            logger.error('Remove ' + fp + 'failed. ' + str(e) + trbk(e))
            raise e  # needed for undoing HK changes

    def schematicWipe(self):
        """
        does the scheme-specific remove-all
        """
        # logger.debug()
        pp = self.transformpath (self._poolpath)
        if not op.exists(pp):
            return
        try:
            res, msg = delete_from_server(self._poolurn, 'pool')
            if res != 'FAILED':
                shutil.rmtree(pp)
                os.mkdir(pp)
            else:
                logger.error(msg)
                raise msg
        except Exception as e:
            err  = 'remove-mkdir ' + self._poolpath + \
                ' failed. ' + str(e) + trbk(e)
            logger.error(err)
            raise e

    def transformpath(self, path):
        """ override this to changes the output from the input one (default) to something else.

        """
        if basepoolpath != '':
            if path[0] == '/':
                path = basepoolpath + path
            else:
                path = basepoolpath + '/' + path
        return path

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """
