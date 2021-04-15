# -*- coding: utf-8 -*-
from ..pns.jsonio import getJsonObj
from ..pns.fdi_requests import urn2fdiurl, save_to_server, read_from_server, delete_from_server
from ..pns.httppool_server import WebAPI
from .urn import Urn, makeUrn
from ..dataset.odict import ODict
from ..dataset.dataset import TableDataset
from ..dataset.serializable import serialize
from .productpool import ProductPool, ManagedPool
from .poolmanager import PoolManager
from .localpool import LocalPool
from .productref import ProductRef
from ..utils.common import pathjoin, trbk, lls, fullname

import filelock
import shutil
import os
import builtins
from itertools import chain
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


class HttpClientPool1(ProductPool):
    """ the pool will save all products on a remote server.


    Housekeeping done by old code of LocalPool. To be deprecated.
    """

    def __init__(self, poolpath_local=None, **kwds):
        """ Initialize connection to the remote server. creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files on server if not exist.

        poolpath_local: sets where to stotr housekeeping data locally. default is None, using PoolManager.PlacePaths['file']
        """
        # print(__name__ + str(kwds))
        #self._poolpath_local = poolpath_local
        super(HttpClientPool1, self).__init__(**kwds)
        self.setPoolpath_local(poolpath_local)

    def setup(self):
        """ Sets up HttpPool interals.

        Make sure that self._poolname and self._poolurl are present.
        """

        if not hasattr(self, '_poolpath_local') or not self._poolpath_local:
            return True
        if super().setup():
            return True

        real_poolpath = self.transformpath(self._poolname)
        logger.debug('real_poolpath '+real_poolpath)
        if not op.exists(real_poolpath):
            # os.mkdir(real_poolpath)
            os.makedirs(real_poolpath)
        c, t, u = self.readHK()

        logger.debug('created ' + self.__class__.__name__ + ' ' + self._poolname +
                     ' at ' + real_poolpath + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)
        return False

    @property
    def poolpath_local(self):
        """ for property getter
        """
        return self.getPoolpath_local()

    @poolpath_local.setter
    def poolpath_local(self, poolpath_local):
        """ for property setter
        """
        self.setPoolpath_local(poolpath_local)

    def getPoolpath_local(self):
        """ returns the path where the client stores local data."""
        return self._poolpath_local

    def setPoolpath_local(self, poolpath_local):
        """ Replaces the current poolpath_local of this pool.
        """
        s = (not hasattr(self, '_poolpath_local')
             or not self._poolpath_local)
        self._poolpath_local = PoolManager.PlacePaths['file'] if poolpath_local is None else poolpath_local
        # call setup only if poolpath_local was None
        if s:
            self.setup()

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

    def schematicSave(self, resourcetype, index, data, tag=None, **kwds):
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

    def schematicLoad(self, resourcetype, index, serialized=False):
        """
        does the scheme-specific part of load.
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


class HttpClientPool2(LocalPool):
    """ the pool will save all products on a remote server.

    Housekeeping delegated to LocalPool.
    """

    def __init__(self, poolpath_local=None, **kwds):
        """ Initialize connection to the remote server. creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files on server if not exist.

        poolpath_local: sets where to stotr housekeeping data locally. default is None, using PoolManager.PlacePaths['file']
        """
        # print(__name__ + str(kwds))
        #self._poolpath_local = poolpath_local
        super(HttpClientPool2, self).__init__(**kwds)
        self.setPoolpath_local(poolpath_local)

    def setup(self):
        """ Sets up HttpPool interals.

        Make sure that self._poolname and self._poolurl are present.
        """

        if not hasattr(self, '_poolpath_local') or not self._poolpath_local:
            return True
        if super().setup():
            return True

        return False

    @property
    def poolpath_local(self):
        """ for property getter
        """
        return self.getPoolpath_local()

    @poolpath_local.setter
    def poolpath_local(self, poolpath_local):
        """ for property setter
        """
        self.setPoolpath_local(poolpath_local)

    def getPoolpath_local(self):
        """ returns the path where the client stores local data."""
        return self._poolpath_local

    def setPoolpath_local(self, poolpath_local):
        """ Replaces the current poolpath_local of this pool.
        """
        s = (not hasattr(self, '_poolpath_local')
             or not self._poolpath_local)
        self._poolpath_local = PoolManager.PlacePaths['file'] if poolpath_local is None else poolpath_local
        # call setup only if poolpath_local was None
        if s:
            self.setup()

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

    def doSave(self, resourcetype, index, data, tag=None, **kwds):
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
                l = super().writeHK(fp0)
                logger.debug('Saved to server done, HK written in local done')
            logger.debug('Product written in remote server done')
        except IOError as e:
            logger.error('Save ' + fp + 'failed. ' + str(e) + trbk(e))
            raise e  # needed for undoing HK changes
        return l

    def doLoad(self, resourcetype, index, serialized=False):
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

    def doRemove(self, resourcetype, index):
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

    def doWipe(self):
        """
        does the scheme-specific remove-all
        """
        # logger.debug()
        pp = self.transformpath(self._poolname)

        res, msg = delete_from_server(None, self._poolurl, 'pool')
        if res == 'FAILED':
            logger.error(msg)
            raise Exception(msg)
        try:
            super().doWipe()
        except IOError as e:
            err = 'remove-mkdir ' + pp + \
                ' failed. ' + str(e) + trbk(e)
            logger.error(err)
            raise e


def toserver(self, method, *args, **kwds):
    def mkv(v):
        t = type(v).__name__
        if t in vars(builtins):
            vs = str(v) + ':' + t
        else:
            vs = serialize(v)+':' + t
        return vs
    argsexpr = (mkv(v) for v in args)
    kwdsexpr = ((str(k), mkv(v)) for k, v in kwds.items())
    apipath = method + '/' + \
        '/'.join(chain(('|'.join(argsexpr),), chain(*kwdsexpr)))
    urn = 'urn:::0'  # makeUrn(self._poolname, typename, 0)

    logger.debug("READ PRODUCT FROM REMOTE===> " + urn)
    res, msg = read_from_server(urn, self._poolurl, apipath)
    if res == 'FAILED':
        if method in msg:
            raise TypeError(msg)
        raise IOError('Executing ' + method + ' failed.  ' + msg)
    return res


def toServer(method_name=None):
    """ decorator to divert local calls to server and return what comes back.

    """
    def inner(*sf):
        """ [self], fun """
        fun = sf[-1]

        def wrapper(*args, **kwds):
            return toserver(args[0],
                            method_name if method_name else fun.__name__,
                            *args[1:],
                            **kwds)
        return wrapper
    return inner


class HttpClientPool(ProductPool):
    """ the pool will save all products on a remote server.
    """

    def __init__(self, **kwds):
        """ Initialize connection to the remote server. creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files on server if not exist.

        """
        # print(__name__ + str(kwds))
        super(HttpClientPool, self).__init__(**kwds)

    def setup(self):
        """ Sets up HttpPool interals.

        Make sure that self._poolname and self._poolurl are present.
        """

        if not hasattr(self, '_poolpath_local') or not self._poolpath_local:
            return True
        if super().setup():
            return True

        return False

    # @toServer()
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

    def schematicSave(self, products, tag=None, geturnobjs=False, serialized=False, **kwds):
        """
        does the media-specific saving to remote server.
        """

        alist = issubclass(products.__class__, list)
        if not alist:
            productlist = [products]
        else:
            productlist = products

        if len(productlist) == 0:
            return []
        # only type and poolname in the urn will be used
        urn = makeUrn(typename=fullname(productlist[0]),
                      poolname=self._poolname, index=0)
        sv = save_to_server(productlist, urn, self._poolurl, tag)
        if sv['result'] == 'FAILED':
            logger.error('Save %d products to server failed. Message from %s: %s' % (
                len(productlist), self._poolurl, sv['msg']))
            raise Exception(sv['msg'])
        else:
            urns = sv['result']
        logger.debug('Product written in remote server done')
        res = []
        if geturnobjs:
            if serialized:
                # return the URN string.
                res = urns
            else:
                res = [Urn(urn=u, poolurl=self._poolurl) for u in urns]
        else:
            for u, prd in zip(urns, productlist):
                if serialized:
                    rf = ProductRef(urn=Urn(urn=u, poolurl=self._poolurl),
                                    poolname=self._poolname)
                    # return without meta
                    res.append(rf)
                else:
                    # it seems that there is no better way to set meta
                    rf = ProductRef(urn=Urn(urn=u, poolurl=self._poolurl),
                                    poolname=self._poolname, meta=prd.getMeta())
                    res.append(rf)
        logger.debug('%d product(s) generated %d %s: %s.' %
                     (len(productlist), len(res), 'Urns ' if geturnobjs else 'prodRefs', lls(res, 200)))
        if alist:
            return serialize(res) if serialized else res
        else:
            return serialize(res[0]) if serialized else res[0]

    def schematicLoad(self, resourcetype, index, serialized=False):
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

    def schematicRemove(self, urn=None, resourcetype=None, index=None):
        """
        does the scheme-specific part of removal.

        urn or (resourcetype, index)
        """
        if urn is None:
            if resourcetype is None or index is None:
                raise ValueError()
            urn = makeUrn(self._poolname, resourcetype, index)
        res, msg = delete_from_server(urn, self._poolurl)
        if res == 'FAILED':
            logger.error('Remove from server ' + self._poolname +
                         ' failed. Caused by: ' + msg)
            raise IOError(msg)
        return res

    def schematicWipe(self):
        """
        does the scheme-specific remove-all
        """

        res, msg = delete_from_server(None, self._poolurl, 'pool')
        if res == 'FAILED':
            logger.error(msg)
            raise Exception(msg)

    @toServer(method_name='select')
    def schematicSelect(self,  query, results=None):
        """
        Returns a list of references to products that match the specified query.
        """
        # return self.toserver('select', query, results=results)

    @toServer()
    def dereference(self, ref):
        """
        Decrement the reference count of a ProductRef.
        """

        # return self.toserver('dereference', ref)

    @toServer()
    def exists(self, urn):
        """
        Determines the existence of a product with specified URN.
        """

        # return self.toserver('exists', urn)

    @toServer()
    def getPoolpath(self):
        """
        Returns poolpath of the server pool, if available.
        """

    @toServer()
    def getProductClasses(self):
        """
        Returns all Product classes found in this pool.
        mh: returns an iterator.
        """
        # return self.toserver('getProductClasses')

    @toServer()
    def getReferenceCount(self, ref):
        """
        Returns the reference count of a ProductRef.
        """
        return self.toserver('getReferenceCount', ref)

    @toServer()
    def isAlive(self):
        """
        Test if the pool is capable of responding to commands.
        """
        # return self.toserver('isAlive')

    @toServer()
    def isEmpty(self):
        """
        Determines if the pool is empty.
        """

        # return self.toserver('isEmpty')

    def meta(self,  urn):
        """
        Loads the meta-data belonging to the product of specified URN.
        """

        # return self.toserver('meta', urn)

    @toServer()
    def reference(self, ref):
        """
        Increment the reference count of a ProductRef.
        """
        # return self.toserver('reference', ref)

    @toServer()
    def getCount(self, typename):
        """
        Return the number of URNs for the product type.
        """
        # return self.toserver('getCount', typename)

    @toServer()
    def getTags(self, urn=None):
        """ 
        Get all of the tags that map to a given URN.
        Get all known tags if urn is not specified.
        mh: returns an iterator.
        """
        raise NotImplementedError

    @toServer()
    def getTagUrnMap(self):
        """
        Get the full tag->urn mappings.
        mh: returns an iterator
        """
        raise NotImplementedError

    @toServer()
    def getUrn(self, tag):
        """
        Gets the URNs corresponding to the given tag. Returns an empty list if tag does not exist.
        """
        raise NotImplementedError

    @toServer()
    def getUrnObject(self, tag):
        """
        Gets the URNobjects corresponding to the given tag.
        """
        raise NotImplementedError

    @toServer()
    def removekey(self, key, themap, thename, othermap, othername):
        """
        Remove the given key.
        """
        raise NotImplementedError

    @toServer()
    def removeTag(self, tag):
        """
        Remove the given tag from the tag and urn maps.
        """
        raise NotImplementedError

    @toServer()
    def removeUrn(self, urn):
        """
        Remove the given urn from the tag and urn maps.
        """
        raise NotImplementedError

    @toServer()
    def setTag(self, tag,  urn):
        """
        Sets the specified tag to the given URN.
        """
        raise NotImplementedError

    @toServer()
    def tagExists(self, tag):
        """
        Tests if a tag exists.
        """
        raise NotImplementedError
