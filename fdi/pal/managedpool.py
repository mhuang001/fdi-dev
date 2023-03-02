# -*- coding: utf-8 -*-

from . import dicthk
from ..dataset.classes import Classes
from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize, Class_Look_Up
from .urn import Urn, parseUrn, parse_poolurl, makeUrn
from .versionable import Versionable
from ..utils.common import (fullname, lls, trbk, pathjoin,
                            logging_ERROR,
                            logging_WARNING,
                            logging_INFO,
                            logging_DEBUG
                            )
from .productref import ProductRef
from .query import AbstractQuery, MetaQuery, StorageQuery
from .productpool import ProductPool
from collections import OrderedDict, ChainMap
from functools import lru_cache
import logging
import filelock
import getpass
import os
import sys

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    from urllib.parse import urlparse
else:
    PY3 = False
    from urlparse import urlparse

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


Lock_Path_Base = '/tmp/fdi_locks_' + getpass.getuser()
# lock time-out
locktout = 10


def makeLockpath(direc, op='w'):
    """ returns the appropriate path to put lock file.

    creats the path if non-existing. Set lockpath-base permission to all-modify so other fdi users can use.
    op: 'r' for readlock no-reading) 'w' for writelock (no-writing)
    """
    if not os.path.exists(Lock_Path_Base):
        os.makedirs(Lock_Path_Base, mode=0o777)

    lp = pathjoin(Lock_Path_Base, direc.replace('/', '_'))

    return lp+'.read' if op == 'r' else lp+'.write'


def _eval(code='', m='', **kwds):
    """ evaluate compiled code with given local vars. """
    try:
        res = eval(code)
    except NameError:
        res = False
        logger.debug("Evaluation error: %s. Traceback %s" %
                     (str(e), trbk(e)))

    return res


# Do not include leading or trailing whitespace as they are not guarantteed.
MetaData_Json_Start = '{"_ATTR_meta":'
MetaData_Json_End = '"_STID": "MetaData"}'

# DictHk must be on te left


class ManagedPool(dicthk.DictHk):
    """ A ProductPool that manages its internal house keeping. """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        # {type|classname -> {'sn:[sn]'}}

    def setup(self):
        """ Sets up interal machiney of this Pool,
        but only if self._poolname and self._poolurl are present,
        and other pre-requisits are met.

        Subclasses should implement own setup(), and
        make sure that self._poolname and self._poolurl are present with ``

        if <pre-requisit not met>: return True
        if super().setup(): return True

        # super().setup() has done its things by now.
        <do setup>
        return False
``
        returns: True if not both  self._poolname and self._poolurl are present.

        """

        if super().setup():
            return True
        # new ##
        self._dTypes = dict()

        return False

    def getPoolpath(self):
        """
        Gets the poolpath of this pool.

        poolpath is usually derived from poolurl received from ``PoolManager`` during initialization.
        """
        return self._poolpath

    def lockpath(self, op='w'):
        """ Make lock path using transformed poolname as name.

        """
        return makeLockpath(self.transformpath(self._poolname), op)

    @ lru_cache(maxsize=32)
    def transformpath(self, path):
        """ override this to changes the output from the input one (default) to something else.

        """
        if path is None:
            return None
        base = self._poolpath
        if base != '':
            if path[0] == '/':
                path = base + path
            else:
                path = base + '/' + path
        return path

    def getCacheInfo(self):
        info = {}
        for i in ['transformpath']:
            info[i] = getattr(self, i).cache_info()

        return info

    def dereference(self, ref):
        """
        Decrement the reference count of a ProductRef.
        """
        # new ###
        poolname, dt, sn = parseUrn(urn, int_index=True)
        # assert self._urns[ref.urn]['refcnt'] == self._dType[dt]['sn'][sn]['refcnt']
        r = self._dType[dt]['sn'][sn]
        if r['refcnt'] == 0:
            raise ValueError('Cannot deref below 0.')
        else:
            r['refcnt'] -= 1
        # /new ###
        # self._urns[ref.urn]['refcnt'] -= 1

    def exists(self, urn, resourcetype=None, index=None):
        """
        Determines the existence of a product with specified URN.
        """
        # new ###
        try:
            urn, datatype, sn = self.get_missing(
                urn, resourcetype, index, no_check=True)
        except KeyError:
            return False
        # return True
        # /new#
        try:
            return int(sn) in self._dTypes[datatype]['sn']
        except (TypeError):
            return False

    def getProductClasses(self):
        """
        Returns all Product classes found in this pool.
        mh: returns an iterator.
        """
        # new ###
        # assert list(self._classes.keys()) == list(self._dTypes.keys())

        return self._dTypes.keys()

    def getCount(self, typename=None):
        """
        Return the number of URNs for the product type.
        """
        try:
            # new ###
            # assert len(self._classes[typename]['sn']) == len(
            # self._dTypes[typename]['sn'])
            if typename:
                return len(self._dTypes[typename]['sn'])
            else:
                return sum(len(dt['sn']) for dt in self._dTypes.values())
        except KeyError:
            return 0

    def doSave(self, resourcetype, index, data, tags=None, serialize_in=True, **kwds):
        """ to be implemented by subclasses to do the action of saving
        """
        raise (NotImplementedError)

    def getReferenceCount(self, ref):
        """
        Returns the reference count of a ProductRef.
        """
        # new ###
        poolname, dt, sn = parseUrn(urn, int_index=False)
        _snd = self._dType[dt]['sn'][sn]
        # assert self._urns[ref.urn]['refcnt'] == _snd['refcnt']
        return _snd['refcnt']
        # /new ###
        # return self._urns[ref.urn]['refcnt']

    def isEmpty(self):
        """
        Determines if the pool is empty.
        """
        # new ###
        # assert len(self._urns) == len(self._dTypes)
        # return len(self._urns) == 0
        return len(self._dTypes) == 0

    def loadDescriptors(self, urn, resourcetype=None, index=None):
        """
        Loads the descriptors belonging to specified URN.
        """
        # new ###
        urn, datatype, sn = self.get_missing(urn, resourcetype, index)
        return self._dTypes
        # return self._urns[urn]

    def readHK():
        """ Subclass should overide this.

        Returns
        -------
        tuple
          Of dicts that are the legacy `self._classes`, `self._tags`,
           `self._urns`, and
                    `self._dTypes`, `self._dTags`

        """
        raise NotImplementedError()

    def setMetaByUrn(self, start, end, urn=None, datatype=None, sn=None):
        """
        Sets the location of the meta data of the specified data to the given URN or a pair of data type and serial number.

        :data: usually un/serialized Product.

        Return
        :urn: stirng
        :datatype: class name
        :sn: serial number in string.
        """

        raise NotImplementedError()

    def getMetaByUrn(self, urn=None, resourcetype=None, index=None):
        """
        Get all of the meta data belonging to a product of a given URN.

        mh: returns an iterator.
        """
        raise NotImplemented

    def meta(self, *args, **kwds):
        """
        Loads the meta-data info belonging to the product of specified URN.
        """
        return self.getMetaByUrn(*args, **kwds)

    def reference(self, ref):
        """
        Increment the reference count of a ProductRef.
        """
        # new ###
        poolname, dt, sn = parseUrn(ref.urn, int_index=True)
        _snd = self._dType[dt]['sn'][sn]
        if 'refcnt' not in _snd:
            _snd['refcnt'] = 0
        # assert self._urns[ref.urn]['refcnt'] == _snd['refcnt']
        _snd['refcnt'] += 1
        # /new ###
        if 0:
            if 'refcnt' not in self._urns:
                self._urns['refcnt'] = 0
            self._urns[ref.urn]['refcnt'] += 1

    def saveOne(self, prd, tag, geturnobjs, serialize_in, serialize_out, res, **kwds):
        """
        Save one product.

            # get the latest HK

        Parameters
        ----------
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

        Return
        ------
        `list` of the following:
        `ProductRef`. `Urn` if `geturnobjs` is set. if`serialze_out` is set for `ProductRef` no product metadata is stored in the returned instance.
        The result is also stored in the `re` parameter.
        """
        if serialize_in:
            pn = fullname(prd)
            cls = prd.__class__
        else:
            # prd is json. extract prod name
            # '... "_STID": "Product"}]'
            pn = prd.rsplit('"', 2)[1]
            cls = Class_Look_Up[pn]
            pn = fullname(cls)

        with filelock.FileLock(self.lockpath('w')), \
                filelock.FileLock(self.lockpath('r')):
            # some new ####
            self._dTypes, self._dTags = tuple(
                self.readHK().values())

            # new+old NORMALIZE TAGS###
            if tag is None:
                tags = []
            elif issubclass(tag.__class__, str):
                tags = [tag]
            elif issubclass(tag.__class__, list):
                tags = tag
            else:
                raise TypeError('Bad type for tag: %s.' %
                                tag.__class__.__name__)
            # new ####
            self._dTypes, self._dTags, _sn = \
                dicthk.populate_pool2(tags, pn, sn=None,
                                      dTypes=self._dTypes, dTags=self._dTags)

            urn = makeUrn(poolname=self._poolname, typename=pn, index=_sn)
            try:
                # save prod and HK
                self.doSave(resourcetype=pn,
                            index=_sn,
                            data=prd,
                            tags=tags,
                            serialize_in=serialize_in,
                            serialize_out=serialize_out,
                            **kwds)
            except ValueError as e:
                msg = 'product ' + urn + ' saving failed.' + str(e) + trbk(e)
                logger.debug(msg)
                # some new ##
                self._dTypes, self._dTags = tuple(
                    self.readHK().values())
                raise e

        if geturnobjs:
            if serialize_out:
                # return the URN string.
                res.append(urn)
            else:
                res.append(Urn(urn, poolurl=self._poolurl))
        else:
            rf = ProductRef(urn=Urn(urn, poolurl=self._poolurl),
                            poolmanager=self._poolmanager)
            if serialize_out:
                # return without meta
                res.append(rf)
            else:
                # it seems that there is no better way to set meta
                rf._meta = prd.getMeta()
                res.append(rf)

    def schematicSave(self, products, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, asyn=False, **kwds):
        """ do the scheme-specific saving.

        Parameters
        ----------
        product : BaseProduct, list
            Product or a list of them or '[ size1, prd, size2, prd2, ...]'.
        tag : str, list
            If given a tag, all products will be having this tag.
        If a list tags are given to every one product then the
        number of tags must not be the same to that of `product`. If
        they are equal, each tag is goven to the product at the same
        index in the `product` list.
        serialize_out : bool
            if `True` returns contents in serialized form.
        serialize_in : bool
            If set, product input is serialized.

        Returns
        -------
        ProductRef: Product reference.
        Urn: If `geturnobjs` is set.
        str: If `serialze_out` is set, serialized form of `ProductRef` or `URN`.
        list: `list` of the above of input is a list.
        """

        res = []
        alist = issubclass(products.__class__, list)
        json_list = False

        if alist:
            if isinstance(tag, list) and len(tag) != len(products):
                # make a list of tags to ','-separated tags
                tag = ','.join(t for t in tag if t)
            if isinstance(tag, str) or tag is None:
                tag = [tag] * len(products)

        if serialize_in:
            if not alist:
                prd = products
                self.saveOne(prd, tag, geturnobjs,
                             serialize_in, serialize_out, res, **kwds)
            else:
                if asyn:
                    prd = products
                    self.asyncSave(prd, tag, geturnobjs,
                                   serialize_in, serialize_out, res, **kwds)
                else:
                    for prd, t in zip(products, tag):
                        # result is in res
                        self.saveOne(prd, t, geturnobjs,
                                     serialize_in, serialize_out, res, **kwds)
        else:
            if alist:
                raise TypeError('a list cannot go with False serialize-in.')
            json_list = products.lstrip().startswith('[')
            if not json_list:
                prd = products
                self.saveOne(prd, tag, geturnobjs,
                             serialize_in, serialize_out, res, **kwds)
            else:
                # parse '[ size1, prd, size2, prd2, ...]'

                last_end = 1
                productlist = []
                comma = products.find(',', last_end)
                while comma > 0:
                    length = int(products[last_end: comma])
                    productlist.append(length)
                    last_end = comma + 1 + length
                    prd = products[comma + 2: last_end+1]
                    self.saveOne(prd, tag, geturnobjs,
                                 serialize_in, serialize_out, res, **kwds)
                    # +2 to skip the following ', '
                    last_end += 2
                    comma = products.find(',', last_end)
        if logger.isEnabledFor(logging_DEBUG):
            sz = 1 if not json_list and not alist else len(
                products) if serialize_in else len(productlist)
            logger.debug('%d product(s) generated %d %s: %s.' %
                         (sz, len(res), 'Urns ' if geturnobjs else 'prodRefs', lls(res, 200)))
        if alist or json_list:
            return serialize(res) if serialize_out else res
        else:
            return serialize(res[0]) if serialize_out else res[0]

    def doLoad(self, resourcetype, index, start=None, end=None, serialize_out=False):
        """ to be implemented by subclasses to do the action of loading
        """
        raise (NotImplementedError)

    def schematicLoad(self, resourcetype, index, start=None, end=None,
                      serialize_out=False):
        """ do the scheme-specific loading
        """

        with filelock.FileLock(self.lockpath('w')):
            ret = self.doLoad(resourcetype=resourcetype,
                              index=index, start=start, end=end,
                              serialize_out=serialize_out)
        return ret

    def doRemove(self, resourcetype, index, asyn=False):
        """ to be implemented by subclasses to do the action of reemoving
        """
        raise (NotImplementedError)

    def schematicRemove(self, urn=None, resourcetype=None, index=None, asyn=False, **kwds):
        """ do the scheme-specific removing URN.
        """

        if not urn and (not resourcetype or not index):
            return 0

        with filelock.FileLock(self.lockpath('w')),\
                filelock.FileLock(self.lockpath('r')):

            urn, datatype, sn = self.get_missing(
                urn, resourcetype, index, no_check=True)

            # get the latest HK
            # some new ####
            self._dTypes, self._dTags = tuple(
                self.readHK().values())
            # c, t, u = self._classes, self._tags, self._urns
            # if urn not in u:
            #     raise ValueError(
            #         '%s not found in pool %s.' % (urn, self.getId()))
            datatypes, sns, alist = ProductPool.vectorize(datatype, sn)

            self.removeUrn(urn, datatype=datatype, sn=sn)

        res = self.doRemove(resourcetype=datatypes, index=sns, asyn=asyn)

        res1 = res if alist else [res]
        for i, r in enumerate(res1):
            if r is None:
                msg = f'product {urn[i]} removal failed.'
                if isinstance(self, (LocalPool, MemPool, HTTPClientpool)):
                    self._dTypes, self._dTags = tuple(
                        self.readHK().values())
                    if getattr(self, 'ignore_error_when_delete', False):
                        raise
                    else:
                        logger.warning(msg)

                    # can only do one at a time
                    break
                elif isinstance(self, (PublicClientPool)):
                    self.getPoolInfo(update_hk=True)
        return res if alist else res[0]

    def getTags(self, urn=None, datatype=None, sn=None, asyn=False, **kwds):
        """ do the scheme-specific getting a tag or tags.
        """

        with filelock.FileLock(self.lockpath('w')),\
                filelock.FileLock(self.lockpath('r')):

            # the real thing.
            if hasattr(self, 'doGetTags'):
                self.doGetTags(urn=urn, asyn=asyn, **kwds)
            # update H/K tables
            res = super().getTags(urn=urn, datatype=datatype, sn=sn, **kwds)

            return res

    def removeTag(self, tag=None, asyn=False, **kwds):
        """ do the scheme-specific removing a tag or tags.
        """

        if not tag:
            return 0

        with filelock.FileLock(self.lockpath('w')),\
                filelock.FileLock(self.lockpath('r')):

            # the real thing.
            if hasattr(self, 'doGetTags'):
                self.doRemoveTag(tag, asyn=asyn, **kwds)
            # remove from H/K tables
            res = super().removeTag(tag)

            return res

    def doWipe(self, keep=False):
        """ to be implemented by subclasses to do the action of wiping.
        """
        raise (NotImplementedError)

    def schematicWipe(self, keep=True, asyn=False):
        """ do the scheme-specific wiping

        """
        with filelock.FileLock(self.lockpath('w')),\
                filelock.FileLock(self.lockpath('r')):
            # new ##
            self._dTypes.clear()
            self._dTags.clear()
            # /new ##
            try:
                res = self.doWipe(keep=keep)
            except ValueError as e:
                msg = f'Wiping {self.poolname} failed. {e} traceback: {trbk(e)}'
                if getattr(self, 'ignore_error_when_delete', False):
                    logger.warning(msg)
                else:
                    raise
        return res

    def meta_filter(self, q, typename=None, reflist=None, urnlist=None, snlist=None, datatypes=None):
        """ returns filtered collection using the query.

        q is a MetaQuery
        valid inputs: typename and ns list; productref list; urn list; datatypes dict.

        :typename: data type (class name)
        :reflist: list of ProductRefs
        :urnlist: list of URNs
        :datatypes:  dict of {typename:sn_list}
        """

        ret = []
        qw = q.getWhere()

        if reflist:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                for ref in reflist:
                    refmet = ref.getMeta()
                    m = refmet if refmet else self.getMetaByUrn(ref.urn)
                    if _eval(code=code, m=m):
                        ret.append(ref)
                return ret
            else:
                for ref in reflist:
                    refmet = ref.getMeta()
                    m = refmet if refmet else self.getMetaByUrn(ref.urn)
                    if qw(m):
                        ret.append(ref)
                return ret
        elif urnlist:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                for urn in urnlist:
                    m = self.getMetaByUrn(urn)
                    if _eval(code=code, m=m):
                        ret.append(ProductRef(urn=urn, meta=m,
                                   poolmanager=self._poolmanager))
                return ret
            else:
                for urn in urnlist:
                    m = self.getMetaByUrn(urn)
                    if qw(m):
                        ret.append(ProductRef(urn=urn, meta=m,
                                   poolmanager=self._poolmanager))
                return ret
        elif snlist or datatypes:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                if snlist:
                    datatypes = {typename: snlist}
                for cls in datatypes:
                    snlist = datatypes[cls]
                    for n in snlist:
                        urn = makeUrn(poolname=self._poolname,
                                      typename=typename, index=n)
                        m = self.getMetaByUrn(urn)
                        if _eval(code=code, m=m):
                            ret.append(ProductRef(urn=urn, meta=m,
                                       poolmanager=self._poolmanager))
                return ret
            else:
                if snlist:
                    datatypes = {typename: snlist}
                for cls in datatypes:
                    snlist = datatypes[cls]
                    for n in snlist:
                        urn = makeUrn(poolname=self._poolname,
                                      typename=typename, index=n)
                        m = self.getMetaByUrn(urn)
                        if qw(m):
                            ret.append(ProductRef(urn=urn, meta=m,
                                       poolmanager=self._poolmanager))
                return ret
        else:
            raise ('Must give a list of ProductRef or urn or sn')

    def prod_filter(self, q, cls=None, reflist=None, urnlist=None, snlist=None, datatypes=None):
        """ returns filtered collection using the query.

        q: an AbstractQuery.
        valid inputs: cls and ns list; productref list; urn list; datatypes dict.

        :cls: type. data type
        :reflist: list of ProductRefs
        :urnlist: list of URNs
        :datatypes:  dict of {cls:sn_list}
        """

        ret = []
        # will add query variable (e.g. 'p') to Global name space
        glbs = globals()
        qw = q.getWhere()
        var = q.getVariable()
        if var in glbs:
            savevar = glbs[var]
        else:
            savevar = 'not in glbs'

        if reflist:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                for ref in reflist:
                    glbs[var] = pref.getProduct()
                    if _eval(code=code, m=m):
                        ret.append(ref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
            else:
                for ref in reflist:
                    glbs[var] = pref.getProduct()
                    if qw(m):
                        ret.append(ref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
        elif urnlist:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                for urn in urnlist:
                    pref = ProductRef(urn=urn, poolmanager=self._poolmanager)
                    glbs[var] = pref.getProduct()
                    if _eval(code=code):
                        ret.append(pref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
            else:
                for urn in urnlist:
                    pref = ProductRef(urn=urn, poolmanager=self._poolmanager)
                    glbs[var] = pref.getProduct()
                    if qw(glbs[var]):
                        ret.append(pref)
                if savevar != 'not in glbs':
                    glbs[var] = savevar
                return ret
        elif snlist or datatypes:
            if isinstance(qw, str):
                code = compile(qw, 'qw.py', 'eval')
                if snlist:
                    datatypes = {cls.__name__: snlist}
                for typename in datatypes:
                    snlist = datatypes[typename]
                    cls = Class_Look_Up[typename.rsplit('.', 1)[-1]]
                    for n in snlist:
                        urno = Urn(cls=cls, poolname=self._poolname, index=n)
                        pref = ProductRef(
                            urn=urno, poolmanager=self._poolmanager)
                        glbs[var] = pref.getProduct()
                        if _eval(code=code):
                            ret.append(pref)
                    if savevar != 'not in glbs':
                        glbs[var] = savevar
                return ret
            else:
                if snlist:
                    datatypes = {cls.__name__: snlist}
                for typename in datatypes:
                    snlist = datatypes[typename]
                    cls = glbs[typename]
                    for n in snlist:
                        urno = Urn(cls=cls, poolname=self._poolname, index=n)
                        pref = ProductRef(
                            urn=urno, poolmanager=self._poolmanager)
                        glbs[var] = pref.getProduct()
                        if qw(glbs[var]):
                            ret.append(pref)
                    if savevar != 'not in glbs':
                        glbs[var] = savevar
                return ret
        else:
            raise ('Must give a list of ProductRef or urn or sn')

    def where(self, qw, prod='BaseProduct', urns=None):
        q = AbstractQuery(prod, 'p', qw)
        # if urns is None:
        # new ###
        datatypes = dict((k, list(v['sn'].keys()))
                         for k, v in self._dTypes.items())
        if 0:
            urns = self._urns.keys()
            res = self.prod_filter(q, prod, urnlist=urns)
        # new ###
        res2 = self.prod_filter(q, prod, datatypes=datatypes)

        # assert [r.urn for r in res] == [r.urn for r in res2]
        return [r.urn for r in res2]

    def doSelect(self, query, previous=None):
        """
        to be implemented by subclasses to do the action of querying.
        """
        raise (NotImplementedError)

    def schematicSelect(self,  query, previous=None):
        """
        do the scheme-specific querying.
        """
        is_MetaQ = issubclass(query.__class__, MetaQuery)
        is_AbstQ = issubclass(query.__class__, AbstractQuery)
        if not is_MetaQ and not is_AbstQ:
            raise TypeError('not a Query')
        lgb = Classes.mapping
        t, v, w, a = query.getType(), query.getVariable(
        ), query.getWhere(), query.retrieveAllVersions()
        ret = []
        if previous:
            this = (x for x in previous if x.urnobj.getPoolId()
                    == self._poolname)
            if is_MetaQ:
                ret += self.meta_filter(q=query, reflist=this)
            else:
                ret += self.prod_filter(q=query, reflist=this)
        else:
            # new ##
            # assert list(self._dTypes) == list(self._classes)
            for cname in self._dTypes:
                cls = lgb[cname.rsplit('.', 1)[-1]]
                if issubclass(cls, t):
                    # snlist = self._classes[cname]['sn']
                    # new ###
                    # assert snlist == list(self._dTypes[cname]['sn'])
                    snlist = list(self._dTypes[cname]['sn'])
                    if is_MetaQ:
                        ret += self.meta_filter(q=query, typename=cname,
                                                snlist=snlist)
                    else:
                        ret += self.prod_filter(q=query, cls=cls,
                                                snlist=snlist)

        return ret

    def __repr__(self):
        # co = ', '.join(str(k) + '=' + lls(v, 40)
        #               for k, v in self.__getstate__().items())
        co = ', '.join(str(k)+'=' + (v if issubclass(v.__class__, str) else
                                     f'< {v.__class__.__name__} {len(v)} >')
                       for k, v in self.__getstate__().items())
        return '<'+self.__class__.__name__ + ' ' + co + '>'

    def __getstate__(self):
        """ returns an odict that has all state info of this object.
        Subclasses should override this function.
        """
        return OrderedDict(
            poolname=getattr(self, '_poolname', 'unknown'),
            poolurl=getattr(self, '_poolurl', 'unknown'),
            _dTypes=self._dTypes,
            _dTags=self._dTags,
        )
