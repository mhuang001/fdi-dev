# -*- coding: utf-8 -*-

from ..httppool.session import requests_retry_session
from ..dataset.product import Product, BaseProduct
from ..dataset.classes import Class_Look_Up
from ..dataset.serializable import serialize
from .poolmanager import PoolManager
from .productpool import ProductPool
from .managedpool import ManagedPool
from .productref import ProductRef
from .productstorage import ProductStorage
from .dicthk import HKDBS, populate_pool2
from .urn import makeUrn, parse_poolurl, Urn, parseUrn
from ..pns.public_fdi_requests import read_from_cloud, load_from_cloud, delete_from_server
from ..pns.fdi_requests import ServerError
from ..utils.common import (fullname, lls, trbk,
                            logging_ERROR,
                            logging_WARNING,
                            logging_INFO,
                            logging_DEBUG
                            )

from ..utils.getconfig import getConfig

import logging
from itertools import chain
import sys

logger = logging.getLogger(__name__)
pcc = getConfig()

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
else:
    PY3 = False
    strset = (str, unicode)

"""
Cloud apis classification:
#/%E9%85%8D%E7%BD%AE%E7%AE%A1%E7%90%86
DOC: http://123.56.102.90:31702/api/swagger-ui.html
Problem:
1. No class shown in storage/info API
2. No pattern for pool path, API use poolname+random name instead of pool <scheme>://<place><poolpath>/<poolname>
3. getMetaByUrn(self, urn, resourcetype=None, index=None) What's means resourcetype and index?
"""


def get_Values_From_A_list_of_dicts(res, what, get_list=True, excpt=True):
    """"Returns value(s) of a list of dicts containing key:value.

       If `get_list` is `True` always retur list of
     vals. Missing key returns `None` as val.
     `None` or Empty list gets `None`.
       If `get_list` is `False` try to return the  value of `what`
      in the first element of `res`. Return `None` upon any exception.
    :except: if set (default), throw `KeyError` if the product or `what` key is missing, or 0 is result.
    """
    if not get_list:
        try:
            return res[0]['what']
        except KeyError as e:
            if excpt:
                raise
            else:
                return 0
    if excpt:
        return [r.get(what, None) for r in res]
    else:
        if not res:
            return []
        return [r[what] for r in res]


class PublicClientPool(ManagedPool):

    def __init__(self,  auth=None, client=None, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.

        Parameters
        ----------
        auth : tuple, HTTPBasicAuth, or Authorization
            Authorization for remote pool.
        client : Request or Wrapper
            Mainly used for testing with mock server.
        **kwds :

        Returns
        -------

        """
        # print(__name__ + str(kwds))
        super().__init__(**kwds)
        self.auth = auth
        if client is None:
            client = requests_retry_session()
        self.client = client
        self.getToken()
        self.poolInfo = None

        self.CSDB_LOG = self.loggen()
        """ Generator object to produce latest n CSDB storage log entres."""

    def setup(self):
        """ Sets up HttpPool interals.

        Make sure that self._poolname and self._poolurl are present.
        """

        if super().setup():
            return True

        return False

    def setPoolurl(self, poolurl):
        """ Replaces the current poolurl of this pool.
            For cloud pool, there are also self._cloudpoolpath and self._cloudpoolname
            csdb:///csdb_test_pool
            self._poolpath, self._scheme, self._poolname = '', 'csdb', 'csdb_test_pool'
            self._cloudpoolpath = /csdb_test_pool
        """
        s = (not hasattr(self, '_poolurl') or not self._poolurl)
        self._poolpath, self._scheme, self._place, \
            self._poolname, self._username, self._password = \
            parse_poolurl(poolurl)
        if self._scheme == '' or self._scheme == None:
            self._scheme = 'csdb'
        self._cloudpoolpath = self._poolpath + '/' + self._poolname
        self._poolurl = poolurl
        # call setup only if poolurl was None
        if s:
            self.setup()

    def getPoolpath(self):
        if self._cloudpoolpath:
            return self._cloudpoolpath
        else:
            return self._poolpath

    def getToken(self):
        """Get CSDB acces token.

        Returns
        -------
        str
            Saved or newly gotten token.

        Raises
        ------
        RuntimeError
            Could not get new token.

        """
        err = False
        tokenMsg = None
        self.token = pcc['cloud_token']
        try:
            tokenMsg = read_from_cloud(
                'verifyToken', token=self.token, client=self.client)
        except ServerError as e:
            err = e
            pass
        if (tokenMsg is not None) and tokenMsg['status'] == 500 or err:
            logger.debug('Cloud token %s to be updated.' % self.token[:5])
        else:
            raise

        tokenMsg = read_from_cloud('getToken', client=self.client,
                                   token=self.token)
        self.token = tokenMsg['token']
        logger.debug('Cloud token %s updated.' % self.token[:5])

        return self.token

    def poolExists(self, poolname=None):
        if poolname is None:
            poolname = self.poolname
        try:
            res = read_from_cloud(
                'existPool', poolname=poolname, token=self.token)
            return True
        except ServerError as e:
            if e.code == 1:
                return False
            raise

    def restorePool(self):
        try:
            res = read_from_cloud(
                'restorePool', poolname=self.poolname, token=self.token)
            return True
        except:
            return False

    def loggen(self):
        """ Generator that returns the latest two entries of csdb storage log
        """
        exlog = 0
        last = ''
        cnt = 0
        if exlog:
            logger.info(f'^^^^')
        while True:
            res = read_from_cloud('poolLogInfo', token=self.token)
            if exlog:
                logger.info(f'>>>cnt={cnt} last={last} len={len(res)}')
            lines = []
            latest_i = ''
            for t in res:
                i = t['id'][-6:]
                if exlog:
                    logger.info(f'...i={i}')
                # save the id of the latest log entry
                if latest_i == '':
                    latest_i = i
                    if exlog:
                        logger.info(f'add latest_i==={latest_i}')
                if i == last:
                    if exlog:
                        logger.info(f'm {i}')
                    break
                lines.append(f"CSDB Storage {i} {t['path']}.")
            else:
                # break did not happen. 'last' is not found.
                if exlog:
                    logger.info('last not found')
                if lines:
                    # there must be some missed ones.
                    lines.append('...')

            if lines:
                last = latest_i
                cnt += 1
                if exlog:
                    logger.info('last updated {last}')
            else:
                if exlog:
                    logger.info('last not updated')
            res = f'>>Polling log {cnt}<<\n%s' % '\n'.join(lines)

            yield res

    def log(self):
        """ returns the latest two entries of csdb storage log
        """
        n = next(self.CSDB_LOG)
        if isinstance(n, str):
            n = n.strip()
        return n if n else ''

    def createPool2(self):

        res = read_from_cloud(
            'createPool', poolname=self.poolname, token=self.token)

        return res

    def createPool(self):
        res = self.createPool2()
        return True

    def getPoolInfo(self, update_hk=True, count=False):
        """
        Download, store server storage info.

        PoolInfo schema 1.0 consisted of three maps: classes,
        urns and tags data:. See productpool::ManagedPool::saveOne
            poolname :
                _classes= {dataTypeName: {currentSn:csn, sn=[]}}
                _urns= [{urn: tags[]}]
                _tags= {urns:[]}

        Parameters
        ----------
        update_hk : bool
            If set (default), get full PoolInfo from server and update local HK tables. If not set the result depends on `count`.
        count : bool
            Return count oriented results. Default is False.

        Results
        -------
        dict

            | update_hk | count  |  output     |
            | `True`    | any | Get the updated PoolInfo and save and returns updated PoolInfo |
            | `False`   | `True`  | Get and returns Count-format PoolInfo from `storage/info?getCount=1` |
            | `False`   | `False` | Returns the local PoolInfo in memory. |
        """
        if update_hk:
            res = read_from_cloud(
                'infoPool', pools=self.poolname, getCount=0, token=self.token)
            rdata = res
            if rdata:
                if self._poolname in rdata:
                    ucnt = len(rdata[self._poolname].get('_urns', 0))
                    dpu = rdata[self._poolname]['_urns'] if ucnt else {}
                    for urn, tags in dpu.items():
                        pool, ptype, sn = parseUrn(urn)
                        self._dTypes, self._dTags, sn = \
                            populate_pool2(tags, ptype, sn, self._dTypes,
                                           self._dTags)
                    logger.debug(
                        f'HK updated for the pool {self.poolname}.')
                else:
                    logger.info(
                        f'No pool found by the name {self.poolname}')
                self.poolInfo = rdata
                return rdata
            else:
                logger.info(f'No pool found.')
            return None
        else:
            # update_hk is False
            if count:
                res = read_from_cloud(
                    'infoPool', pools=self.poolname, getCount=1, token=self.token)
                return res
            else:
                return self.poolInfo

    def readHK(self):
        """ read housekeeping data from server """

        self.getPoolInfo(update_hk=True)

        return dict((n, db) for n, db in zip(HKDBS, [
            self._dTypes, self._dTags]))

    def exists(self, urn, update=True):
        """
        Determines the existence of a product with specified URN.

        :update: read the server using `getPoolInfo` w/o updating the HK tbles. Defalut is `False`: only look up in the local cache of `PoolInfo`.
        """

        if update:
            self.getPoolInfo(update_hk=False)
        return urn in self.poolInfo[self._poolname]['_urns']

    def getProductClasses(self, count=True):
        """
        Returns all Product classes found in this pool.

            Ref. doc of `getPoolInfo`.

        Parameters
        -----------
        count : bool

        Returns
        -------
        list:
            of all product types.
        None:
            No such pool.
        """

        if count:
            cnt = self.getPoolInfo(update_hk=False, count=count)
            return list(cnt[self.poolname]['_classes'])
        if self.poolInfo is None:
            return None
        classes = list(self.poolInfo[self.poolname]['_classes'])
        return classes

    def getCount(self, typename=None, update=True):
        """
        Return the number of URNs for the product type in the pool.

        Parameters
        -----------
        update : bool
             Read the latest from server if set (default) or use the local `poolInfo`.
        typename : str, None
            Name of datatype. If is `None` get count of all types.

        Returns
        -------
        int:
            of all product types.
        None:
            No such pool.
        """
        cnt = self.getPoolInfo(update_hk=False, count=update)
        if update:
            # return cnt[self._poolname]['cnt'] if typename is None else cnt[self._poolname]['_classes'].get(typename, 0)
            cp = cnt.get(self._poolname, 0)
            if cp == 0:
                return 0
            return cp.get('_urns', 0) if typename is None else cp['_classes'].get(typename, {'cnt': 0})['cnt']
        return super().getCount(typename)

    def isEmpty(self):
        """
        Determines if the pool is empty.
        """
        res = self.getPoolInfo()
        if issubclass(res.__class__, dict):
            clses = res[self.poolname]['_classes']
            return len(clses) == 0
        else:
            raise ValueError('Error getting PoolInfo ' + str(res))

    def getMetaByUrn(self, urn=None, resourcetype=None, index=None):
        """
        Get all of the meta data belonging to a product of a given URN.

        mh: returns an iterator.
        """
        res = read_from_cloud(requestName='getMeta', urn=urn, token=self.token)
        return res

    def getDataType(self, urn=None):
        """Returns the Datatype of one or a list of URNs.

        Parameters
        ----------
        urn : str, list, None

        Returns
        -------
        dict, list
            all types if `urn` is not given. one or a list of
            datatypes (None if the URN is not found, '' of no
            Datatype.

        Examples
        --------
        FIXME: Add docs.

        """

        if urn is None:
            res = read_from_cloud('getDataType', token=self.token)
            return res

        if isinstance(urn, list):
            alist = True
        else:
            alist = False
            urns = [urn]
        paths = [u[3:].replace(':', '/') for u in urn]
        r = self.get_DataInfo('dataType', paths=paths)
        return r if alist else r[0]

    def getDataInfo(self, what='', paths=None, pool=None,
                    nulltype=True, limit=10000, asyn=False,
                    excpt=True):
        """Returns the CSDB storage information of one or a list of URNs.

        Parameters
        ----------
        what : str
            which item in list to return. e.g. 'urn' means
            a list
            of URNs found in the path. Default '' for all items.
        paths : str, list, None
            part in a path. URNs are allowed. Typical uses: '{poolname}' for a pool,
            or '/{poolname}/{product-type}' for a type of products in a pool,
            or '{poolname}/{product-name}/{index.aka.serial-number}',
            e.g. '/sv1/sv.BaseProduct' for all 'sv.BaseProduct' products in pool 'sv1'.
            Only one  of `paths` and `pool` can be non-empty.
            default is `None`.
        pool : str, None
            Only one  of `paths` and `pool` can be non-empty.
            Default is `None` for `self` pool if `paths` is empty,
            empty if `paths` is not.
        nulltype : bool
            Include None dataType entries. default `True`
        limit : int
            Maximum record number. Default `None` for 10000.
        except: bool
            If set (default), throw `KeyError` if the product or
        `what` key is missing, or 0 is result.
        Returns
        -------
        dict, list
            `None` if `paths` and `pool` are not found. one or a list of
            value for the given `what` key (None if not found).

        Examples
        --------
        FIXME: Add docs.

        """
        pname = self._poolname
        alist = isinstance(paths, (list, tuple))
        if not alist:
            if paths and pool:
                raise ValueError(
                    f"Path '{a}' and pool '{pool}' cannot be both non-empty for getDataInfo.")
            # if both are empty, pool takes self.poolname
            if not pool and not paths:
                pool = pname
            res = read_from_cloud('getDataInfo', token=self.token,
                                  paths=paths, pool=pool, limit=limit)
            # if input is not list the output of each query is not a list
            if not nulltype:
                popped = [res.pop(i) for i in range(
                    len(res)-1, -1, -1) if res[i]['dataType'] is None]
                logger.debug(f'{len(popped)} popped')
            if what:
                r = get_Values_From_A_list_of_dicts(res, what, excpt=excpt)
            else:
                # if path is a loner return the value, else
                # the pool is returned (one element pool, too).
                r = res
            return r
        # alist
        # if both are empty, pool takes self.poolname
        if not pool:
            pool = pname
        res = read_from_cloud('getDataInfo', token=self.token,
                              paths=paths, pool=pool, limit=limit, asyn=asyn)
        # in the output each query is a list[[p,p..],[p,p,...]]
        if not nulltype:
            popped = [q.pop(i) for q in res for i in range(
                len(q)-1, -1, -1) if q[i]['dataType'] is None]
            logger.debug(f'{len(popped)} popped')
        if what:
            bunch = [get_Values_From_A_list_of_dicts(r, what, excpt=excpt)
                     for r in res]
        else:
            bunch = res
        return bunch

    def doSave(self, resourcetype, index, data, tag=None, serialize_in=True, **kwds):
        path = f'/{self._poolname}/{resourcetype}'

        res = load_from_cloud('uploadProduct', token=self.token,
                              products=data, path=path, tags=tag, resourcetype=resourcetype, **kwds)
        return res

    def saveOne(self, prd, tag, geturnobjs, serialize_in, serialize_out, res, check_type=True, **kwds):
        """Save one product.

        Parameters
        ----------
        prd : BaseProduct, str, list
            The product(s) to be saved. It can be a product, a list of
            product or, when `serialize_in` is false, a JSON
            serialized product or list of products.
        tag : string list
             One or a list of strings. Comma is used to separate
             multiple tags in one string.
        geturnobjs : bool
            return URN object(s) instead of ProductRef(s).
        serialize_in : bool
            The input needs to be serialized for saving to a pool.
        serialize_out : bool
            The output is serialized.
        res : list
            the output list when input `prd` is a list.
        check_type : list
            To Check if the remote (CSDB) server has the type of the
            products that are to be saved.
        **kwds :

        Returns
        -------
        ProductRef, URN, list
            One ProductRef or URN object or a list of them. If
            `serialize_in` is true, the output PRoductRef has metadata
            in it.

        Raises
        ------
        ValueError
            Product type not found on the server.

        Examples
        --------
        FIXME: Add docs.


        """

        jsonPrd = prd
        if serialize_in:
            pn = fullname(prd)
            cls = prd.__class__
            jsonPrd = serialize(prd)
        else:
            # prd is json. extract prod name
            # '... "_STID": "Product"}]'
            # pn = prd.rsplit('"', 2)[1]
            cls = Class_Look_Up[pn]
            pn = fullname(cls)

        if check_type:
            if pn not in check_type:
                raise ValueError('No such product type in csdb: ' + pn)

        # targetPoolpath = self.getPoolpath() + '/' + pn
        try:
            # save prod to cloud
            uploadRes = self.doSave(resourcetype=pn,
                                    index=None,
                                    data=jsonPrd if serialize_in else prd,
                                    tag=tag,
                                    serialize_in=serialize_in,
                                    serialize_out=serialize_out,
                                    **kwds)
        except ValueError as e:
            msg = f'product {self.poolname}/{pn} saving failed. {e} {trbk(e)}'
            logger.debug(msg)
            raise e

        self._format_res(uploadRes, geturnobjs, prd, serialize_out, res)

    def _format_res(self, uploadRes, geturnobjs, prd, serialize_out, res):
        """ uploadRes : record of the csdb upload. """
        utype = uploadRes.get('dataType', '')
        if utype == '':
            raise Exception('Upload failed: product "%s" to %s:' % (
                prd.description, self.poolurl) + uploadRes['msg'])

        urn = uploadRes['urn']

        if utype is None:
            logger.warning(
                f'{urn} is uploaded but has no dataType. Upload Datatype definition to fix.')

        if geturnobjs:
            if serialize_out:
                # return the URN string.
                res.append(urn)
            else:
                res.append(Urn(urn))
        else:
            rf = ProductRef(urn=Urn(urn, poolurl=self.poolurl))
            if serialize_out:
                # return without meta
                res.append(rf)
            else:
                # it seems that there is no better way to set meta
                rf._meta = prd.getMeta() if getattr(prd, 'getMeta') else ''
                res.append(rf)

    def asyncSave(self, prds, tags, geturnobjs, serialize_in, serialize_out, res, check_type=[], **kwds):
        jsonPrds = []
        paths = []
        resourcetypes = []
        p0 = f'/{self._poolname}/%s'
        for prd in prds:
            if serialize_in:
                fc = fullname(prd)
                resourcetypes.append(fc)
                jsonPrds.append(serialize(prd))
            else:
                # prd is json. extract prod name
                # '... "_STID": "Product"}]'
                pn = prd.rsplit('"', 2)[1]
                cls = Class_Look_Up[pn]
                fc = fullname(cls)
                resourcetype.append(fc)
                jsonPrds.append(prd)
            paths.append(p0 % fc)

        if check_type:
            for pn in set(resourcetypes):
                if pn not in check_type:
                    raise ValueError('No such product type in cloud: ' + pn)
        # save prods to cloud
        if serialize_in:
            uploadr = load_from_cloud('uploadProduct', token=self.token,
                                      products=jsonPrds, path=paths,
                                      resourcetype=resourcetypes,
                                      tags=tags, asyn=True,
                                      **kwds)
            for i, uploadRes in enumerate(uploadr):
                self._format_res(uploadRes, geturnobjs,
                                 prd, serialize_out, res)
        return res

    def schematicSave(self, products, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, asyn=False, **kwds):
        """ do the scheme-specific saving.

            :serialize_out: if True returns contents in serialized form.
        """
        res = []
        if not PoolManager.isLoaded(self._poolname):  # self.poolExists():
            raise ValueError(f'Pool {self._poolname} is not registered.')

        check_type = self.serverDatatypes

        res = super().schematicSave(products, tag=tag, geturnobjs=geturnobjs,
                                    serialize_in=serialize_in,
                                    serialize_out=serialize_out,
                                    asyn=asyn,
                                    check_type=check_type,
                                    **kwds)
        # XXX refresh currentSn on server
        self.getPoolInfo()

        return res

    def schematicLoad(self, resourcetype, index, start=None, end=None,
                      serialize_out=False):
        """ do the scheme-specific loading
        """

        spn = self._poolname
        poolInfo = self.getPoolInfo()
        try:
            if poolInfo:
                pinfo = poolInfo
                if spn in pinfo:
                    if index in pinfo[spn]['_classes'][resourcetype]['sn']:
                        urn = makeUrn(poolname=spn,
                                      typename=resourcetype, index=index)
                        res = load_from_cloud(
                            'pullProduct', token=self.token, urn=urn)
                        # res is a product like ..dataset.product.Product

                        if issubclass(res.__class__, BaseProduct):
                            if serialize_out:
                                from ..dataset.deserialize import serialize
                                return serialize(res)
                            else:
                                return res
                        else:
                            raise Exception('Load failed: ' +
                                            res.get('msg', lls(res, 999)))
        except Exception as e:
            logger.debug('Load product failed:' + str(e))
            raise e
        logger.debug('No such product:' + resourcetype +
                     ' with index: ' + str(index))
        raise ValueError('No such product:' + resourcetype +
                         ' with index: ' + str(index))

    def doLoad(self, resourcetype, index, start=None, end=None, serialize_out=False):
        """ to be implemented by subclasses to do the action of loading
        """
        raise NotImplementedError

    # def schematicRemove(self, urn=None, resourcetype=None, index=None, asyn=False, **kwds):
    #     """ do the scheme-specific removing.

    #     `resourcetype+index` takes priority over `urn`.
    #     """
    #     prod, sn, urn = self.get_missing(urn, resourcetype, index,
    #                                      no_check=True)
    #     if index is None or index == '':
    #         self.schematicWipe()
    #         return

    #     if issubclass(index.__class__, (list, tuple)):
    #         if asyn:
    #             return
    #         else:
    #             for i, ind in enumerate(index):
    #                 self.doRemove(resourcetype, ind)
    #     else:
    #         # a single product
    #         return self.doRemove(resourcetype, index)

    def doRemove(self, resourcetype, index, asyn=False):
        """ to be implemented by subclasses to do the action of reemoving
        """

        path0 = f'/{self._poolname}'
        datatype, sns, alist = ProductPool.vectorize(resourcetype, index)

        path = [f'{path0}/{f}/{i}' for f, i in zip(datatype, sns)]
        res = read_from_cloud('remove', token=self.token, path=path, asyn=asyn)
        return res

    def XdoAsyncRemove(self, resourcetype, index):
        """ implemented with aio to do the action of removing asynchronously.
        """
        # path = self._cloudpoolpath + '/' + resourcetype + '/' + str(index)

        res = read_from_cloud('remove', token=self.token, path=path)
        if res['code'] and not getattr(self, 'ignore_error_when_delete', False):
            raise ValueError(
                f"Remove product {path} failed: {res['msg']}")
        logger.debug(f"Remove {path} code: {res['code']} {res['msg']}")

        return res

    def doRemoveTag(self, tag, update=True, asyn=False):
        """remove the tags

        Parameters
        ----------
        update : bool
            update internal H/K tables by reading the server. Defaut
            `True`.
        asyn : bool
            doing it in parallel.

        Returns
        -------
        int
            0 means OK.

        Raises
        ------
        ValueError
            Target not found.

        Examples
        --------
        FIXME: Add docs.

        """
        if update:
            self.getPoolInfo(update_hk=True)

        if isinstance(tag, (str, list)):
            res = delete_from_server('delTag', token=self.token, tag=tag)
        else:
            raise ValueError('Tag must be a string or a list of string.')
        return res

    def doWipe(self, keep=True):
        """ to do the action of wiping.

        Parameters
        ----------
        keep : boolean
            If set (default) clean up data and metadata but keep the container object.
        """
        poolname = self._poolname

        # res = read_from_cloud(
        #     'wipePool', poolname=poolname, token=self.token)
        # if res['msg'] != 'success':
        #     raise ValueError('Wipe pool ' + poolname +
        #                      ' failed: ' + res['msg'])
        # return
        cnt = self.getProductClasses(count=True)
        path = None
        res = []

        for clazz in cnt:
            path = f'/{poolname}/{clazz}'

            r = read_from_cloud(
                'delDataTypeData', path=path, token=self.token)
            res.append(r)
            logger.debug(f'Removed {path}')
        if not keep:
            # remove the pool object from the DB
            r = read_from_cloud(
                'wipePool', poolname=poolname, token=self.token)
            if r is None:
                logger.debug(f'Done removing {path}')
            else:
                msg = f'Wipe pool {poolname} failed to remove pool.'
                if getattr(self, 'ignore_error_when_delete', False):
                    logger.warning(msg)
                else:
                    raise ServerError(msg)

        return res

    # def acquire_lock(self):
    #     lock_proc_id = socket.gethostname()+'_' + getpass.getuser() + \
    #         '_' + str(os.getpid())
    #     if not getattr(self, 'locks'):
    #         self.locks = {}
    #     if not self.locks:
    #         self.nlocks = 50
    #         self.lock_n = 0
    #     while 1:
    #         self.lock_n = self.lock_n mod self.nlocks
    #         if self.lock_n not in self.lock:
    #             self.lock[self.nlock] = lock_proc_id
    #             self.lockid2lock_n[lock_proc_id] = self.lock_n
    #         self

    def setTag(self, tag, urn):
        """ Set given tag or list of tags to the URN.

        Parameters
        ----------
        :tag: tag or list of tags.
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        if not self.exists(urn):
            raise ValueError('Urn does not exist!')
        if isinstance(tag, (list, str)) and len(tag) > 0:
            # no space in "."
            t = ','.join(tag) if isinstance(tag, list) else tag
            try:
                res = read_from_cloud(
                    'addTag', token=self.token, tag=t, urn=u)
            except ServerError as e:
                msg = f'Set {tag} to {urn} failed: {e}'
                logger.warning(msg)
                raise
            except ValueError as e:
                msg = 'Tag can not be empty or non-string!'
                raise

    def doGetTags(self, urn=None, update=True, **kwds):
        """
        :urn: missing or `None` will have all tags in the pool returned.
        :update: read the server using `getPoolInfo` w/o updating the HK tables. Default is `False`: only look up in the local cache of `PoolInfo`.
        """

        if update:
            self.getPoolInfo()
        # if not urn:
        #     return list(self.poolInfo[self._poolname]['_tags'])
        # ts = self.poolInfo[self._poolname]['_urns'].get(urn)
        # return ts

    def removeTagByUrn(self, tag, urn):
        raise NotImplementedError
        pass

    def tagExists(self, tag):
        """
        Tests if a tag exists.


        Parameters
        ----------
        tag : str, list

        Returns
        -------
        dict, list
            Throw ValueError if `tag` is not given. one or a list of
            results (None if the tag is not found.

        Examples
        --------
        FIXME: Add docs.

        """

        if tag is None:
            raise ValueError('Cannot take None or "" as a tag.')

        try:
            res = read_from_cloud(
                'tagExist', token=self.token, tag=tag)
        except ServerError as e:
            msg = f'Get existance tag failed: {e}'
            logger.warning(msg)
            raise
        return res

    def getUrn(self, tag=None):
        """
        Gets the URNs corresponding to the given tag.


        Parameters
        ----------
        tag : str, list

        Returns
        -------
        dict, list
            all URNs if `tag` is not given. one or a list of
            URNs (None if the tag is not found.

        Examples
        --------
        FIXME: Add docs.

        """

        if tag is None:
            raise ValueError('Cannot take None or "" as a tag.')

        try:
            res = read_from_cloud(
                'getUrn', token=self.token, tag=tag)
        except ServerError as e:
            if e.code == 1 and e.args[0].endswith('fail'):
                # urn doesn't exist
                res = []
            else:
                raise
        return res

    def meta_filter(self, q, typename=None, reflist=None, urnlist=None, snlist=None):
        """ returns filtered collection using the query.

        q is a MetaQuery
        valid inputs: typename and ns list; productref list; urn list
        """
        pass

    def prod_filter(self, q, cls=None, reflist=None, urnlist=None, snlist=None):
        """ returns filtered collection using the query.

        q: an AbstractQuery.
        valid inputs: cls and ns list; productref list; urn list
        """

    def doSelect(self, query, results=None):
        """
        to be implemented by subclasses to do the action of querying.
        """
        raise (NotImplementedError)


# =================SAVE REMOVE LOAD================
# test_getToken2()
# test_poolInfo()
# test_upload()
# test_get()
# test_remove()
# test_multi_upload()
# prd = genProduct(1)
# res = cp.schematicSave(prd)
# cp.schematicRemove('urn:poolbs:20211018:4')

# cp.schematicLoad('fdi.dataset.product.Product', 1)
# cp.schematicLoad('20211018', 5)
