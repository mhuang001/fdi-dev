# -*- coding: utf-8 -*-

from .productpool import ManagedPool, PoolNotFoundError, MetaData_Json_Start, MetaData_Json_End
from ..utils.common import pathjoin, trbk
from .urn import makeUrn, Urn, parseUrn
from ..dataset.deserialize import deserialize

import filelock
from functools import lru_cache
import sys
import shutil
import mmap
import time
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


def wipeLocal(path):
    """
    does the scheme-specific remove-all.

    A new directory at `path` will be created.
    """
    # logger.debug()

    if path == '/':
        raise(ValueError('Do not remove root directory.'))

    try:
        if op.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
    except Exception as e:
        msg = 'remove-mkdir failed. exc: %s trbk: %s.' % (str(e), trbk(e))
        logger.error(msg)
        raise e


class LocalPool(ManagedPool):
    """ the pool will save all products in local computer.

        :makenew: when the pool does not exist, make a new one (````True```; default) or throws `PoolNotFoundError` (```False```).

    """

    def __init__(self, makenew=True, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """
        # print(__name__ + str(kwds))
        self._makenew = makenew  # must preceed setup() in super
        super().__init__(**kwds)

    def setup(self):
        """ Sets up LocalPool interals.

        Make sure that self._poolname and self._poolurl are present.
        """

        if super().setup():
            return True

        real_poolpath = self.transformpath(self._poolname)
        if not op.exists(real_poolpath):
            if self._makenew:
                os.makedirs(real_poolpath)
            else:
                raise PoolNotFoundError('poolname: %r poolurl: %r real_poolpath: %r' % (
                    self._poolname, self._poolurl, real_poolpath))
        self._files = {}
        self._atimes = {}
        self._cached_files = {}

        c, t, u = tuple(self.readHK().values())

        logger.debug('created ' + self.__class__.__name__ + ' ' + self._poolname +
                     ' at ' + real_poolpath + ' HK read.')

        self._classes.update(c)
        self._tags.update(t)
        self._urns.update(u)
        fp0 = self.transformpath(self._poolname)
        self.writeHK(fp0)
        return False

    def readmmap(self, filename,  start=None, end=None, close=False, check_time=False):
        fp = op.abspath(filename)
        if check_time:
            sr = os.stat(fp)
        if check_time and fp in self._atimes and (sr.st_mtime_ns <= self._atimes[fp]):
            # file hasnot changed since last time we read/wrote it.
            return None
        try:
            if 1:  # if fp not in self._files or self._files[fp] is None:
                file_obj = open(fp, mode="r+", encoding="utf-8")
                mmap_obj = mmap.mmap(
                    file_obj.fileno(), length=0, access=mmap.ACCESS_READ)
                fo = mmap_obj
            else:
                fo = self._files[fp]
            if start is None:
                js = fo.read()
            else:
                fo.seek(start)
                js = fo.read(end - start)
        except Exception as e:
            msg = 'Error in HK reading. exc: %s trbk: %s.' % (str(e), trbk(e))
            logging.error(msg)
            raise NameError(msg)
        if 1:  # close:
            fo.close()
            if fp in self._files:
                del self._files[fp]
        else:
            self._files[fp] = fo
        if check_time:
            # save the mtime as the self atime
            self._atimes[fp] = sr.st_mtime_ns
        return js.decode('ascii')

    def readHK(self, hktype=None, serialize_out=False):
        """
        loads and returns the housekeeping data

        hktype: one of 'classes', 'tags', 'urns' to return. default is None to return alldirs
        serialize_out: if True return serialized form. Default is false.
        """
        if hktype is None:
            hks = ['classes', 'tags', 'urns']
        else:
            hks = [hktype]
        fp0 = self.transformpath(self._poolname)

        hk = {}
        for hkdata in hks:
            fp = op.abspath(pathjoin(fp0, hkdata + '.jsn'))
            if op.exists(fp):
                js = self.readmmap(fp, check_time=True)
                if js:
                    if serialize_out:
                        r = js
                    else:
                        from ..dataset.deserialize import deserialize
                        r = deserialize(js)
                    self._cached_files[fp] = js
                else:
                    # the file hasnot changed since last time we r/w it.
                    r = self._cached_files[fp] if serialize_out else \
                        self.__getattribute__('_' + hkdata)
            else:
                if serialize_out:
                    r = '{"_STID":"ODict"}'
                else:
                    from ..dataset.odict import ODict
                    r = ODict()
            hk[hkdata] = r
            assert r is not None
        logger.debug('HK read from ' + fp0)
        if serialize_out:
            return '{%s}' % ', '.join(('"%s": %s' % (k, v) for k, v in hk.items())) if hktype is None else hk[hktype]
        else:
            return hk if hktype is None else hk[hktype]

    def writeJsonmmap(self, fp, data, serialize_in=True, serialize_out=False, close=False, check_time=False, meta_location=False, **kwds):
        """ write data in JSON from mmap file at fp.

        register the file. Leave file open by default `close`.
        data: to be serialized and saved.
        serialize_out: if True returns contents in serialized form.
        :check_time: to check if file has not been written since we did last time. Default `False`.
        :meta_location: return the start and end offsets of metadata in data JSON.  Default `False`.
        :return:
        int bytes written. If `meta_location` is ```True```, adding int int start and end point offsets of metadata in seriaized data.
        """
        from ..dataset.serializable import serialize

        js = serialize(data, **kwds) if serialize_in else data
        #start = end = None
        if meta_location:
            # locate metadata
            start = js.find(MetaData_Json_Start, 0)
            # make end relative to file start
            end = js.find(MetaData_Json_End, start) + start
            start += len(MetaData_Json_Start)
            end += len(MetaData_Json_End)

        fp = op.abspath(fp)
        if 1:  # fp not in self._files or self._files[fp] is None:
            file_obj = open(fp, mode="w+", encoding="utf-8")
            # with mmap.mmap(file_obj.fileno(), length=0, access=mmap.ACCESS_WRITE) as mmap_obj:
        else:
            file_obj = self._files[fp]
        file_obj.seek(0)

        # file_obj.resize(len(js))
        file_obj.truncate(0)
        file_obj.write(js)
        # file_obj.flush()
        close = 1
        if close:
            file_obj.close()
            if fp in self._files:
                del self._files[fp]
        else:
            self._files[fp] = file_obj
        if check_time:
            # save the mtime as the self atime
            sr = os.stat(fp)
            os.utime(fp, ns=(sr.st_atime_ns, sr.st_mtime_ns))
            self._atimes[fp] = sr.st_mtime_ns
            self._cached_files[fp] = js
        l = len(js)
        logger.debug('JSON saved to: %s %d bytes' % (fp, l))
        if meta_location:
            return l, start, end
        else:
            return l

    def writeHK(self, fp0=None):
        """ save the housekeeping data to disk
        """
        if fp0 is None:
            fp0 = self._poolpath + '/' + self._poolname
        l = 0
        for hkdata in ['classes', 'tags', 'urns']:
            fp = pathjoin(fp0, hkdata + '.jsn')
            l += self.writeJsonmmap(fp, self.__getattribute__('_' + hkdata),
                                    check_time=True)
        return l

    def setMetaByUrn(self, start, end, urn):
        """
        Sets the location of the meta data of the specified data to the given URN.

        :data: usually serialized Product.
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        if u not in self._urns:
            raise ValueError(urn + ' not found in pool ' + self._poolname)
        # char offset of the start and end points of metadata
        if start >= 0 and end > 0:
            mt = [start, end]
        else:
            mt = [None, None]
        self._urns[u]['meta'] = mt

    @ lru_cache(maxsize=1024)
    def getMetaByUrnJson(self, urn, resourcetype, index):

        # deserialize(prd[start+len(MetaData_Json_Start):end+len(MetaData_Json_End)])
        try:
            start, end = tuple(self._urns[urn]['meta'])
        except KeyError as e:
            msg = f"Trouble with {self._poolname}._urns[urn]['meta']"
            logger.debug(msg)
            raise e
        js = self.schematicLoad(resourcetype=resourcetype,
                                index=index, start=start, end=end,
                                serialize_out=True)

        return js

    def getCacheInfo(self):
        info = super().getCacheInfo()
        for i in ['getMetaByUrnJson', 'transformpath']:
            info[i] = getattr(self, i).cache_info()

        return info

    def getMetaByUrn(self, urn, resourcetype=None, index=None):
        """ 
        Get all of the meta data belonging to a product of a given URN.

        mh: returns an iterator.
        """
        if urn is None:
            return None  # TODO self._meta.keys()
        #uobj = Urn(urn=urn)
        if resourcetype is None or index is None:
            poolname, resourcetype, index = parseUrn(urn)
        m = self.getMetaByUrnJson(urn, resourcetype=resourcetype,
                                  index=index)
        return deserialize(m)  # self._urns[urn]['meta']

    def doSave(self, resourcetype, index, data, tag=None, serialize_in=True, **kwds):
        """
        does the media-specific saving.

        index: int
        """
        fp0 = self.transformpath(self._poolname)
        fp = pathjoin(fp0, quote(resourcetype) + '_' + str(index))
        try:
            # t0 = time.time()
            l, start, end = self.writeJsonmmap(
                fp, data, serialize_in=serialize_in, close=True,
                meta_location=True, **kwds)

            urn = makeUrn(self._poolname, resourcetype, index)
            self.setMetaByUrn(start, end, urn)

            l += self.writeHK(fp0)
            # print('tl %.8f %9d' % (time.time()-t0, l))
            logger.debug('HK written')
        except IOError as e:
            logger.error('Save failed. exc: %s trbk: %s.' % (str(e), trbk(e)))
            raise e  # needed for undoing HK changes
        return l, start, end

    def doLoad(self, resourcetype, index, start=None, end=None, serialize_out=False):
        """
        does the action of loading.

        serialize_out: if True returns contents in serialized form.
        """

        indexstr = str(index)
        pp = self.transformpath(self._poolname) + '/' + \
            resourcetype + '_' + indexstr
        js = self.readmmap(pp, start=start, end=end, close=True)
        if serialize_out:
            r = js
        else:
            from ..dataset.deserialize import deserialize
            r = deserialize(js)

        return r

    def doRemove(self, resourcetype, index):
        """
        does the action of removal of product from pool.
        """
        fp0 = self.transformpath(self._poolname)
        fp = op.abspath(pathjoin(fp0,  quote(resourcetype) + '_' + str(index)))
        try:
            if fp in self._files:
                if self._files[fp]:
                    self._files[fp].flush()
                    self._files[fp].close()
                del self._files[fp]
            os.unlink(fp)
            self.writeHK(fp0)
        except IOError as e:
            logger.error('Remove failed. exc: %s trbk: %s.' %
                         (str(e), trbk(e)))
            raise e  # needed for undoing HK changes
        return 0

    def doWipe(self):
        """
        does the action of remove-all
        """
        for n, f in self._files.items():
            if f:
                f.flush()
                f.close()
        self._files.clear()
        self._atimes.clear()
        self._cached_files.clear()
        self._classes.clear()
        self._tags.clear()
        self._urns.clear()
        # will leave a newly made pool dir
        wipeLocal(self.transformpath(self._poolname))
        return 0

    def getHead(self, ref):
        """ Returns the latest version of a given product, belonging
        to the first pool where the same track id is found.
        """

        raise(NotImplementedError())
