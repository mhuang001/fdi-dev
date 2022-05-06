import logging
import os
from itertools import chain
import sys

from fdi.dataset.arraydataset import ArrayDataset
from fdi.dataset.product import Product, BaseProduct
from fdi.dataset.serializable import serialize
from fdi.pal.poolmanager import PoolManager
from fdi.pal.productpool import ManagedPool
from fdi.pal.productref import ProductRef
from fdi.pal.productstorage import ProductStorage
from fdi.pal.urn import makeUrn, parse_poolurl, Urn, parseUrn
from fdi.pns.public_fdi_requests import read_from_cloud, load_from_cloud, delete_from_server
from fdi.utils.common import fullname, lls, trbk
from fdi.utils.getconfig import getConfig

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
DOC: http://123.56.102.90:31702/api/swagger-ui.html#/%E9%85%8D%E7%BD%AE%E7%AE%A1%E7%90%86
Problem:
1. No class shown in storage/info API
2. No pattern for pool path, API use poolname+random name instead of pool <scheme>://<place><poolpath>/<poolname>
3. getMetaByUrn(self, urn, resourcetype=None, index=None) What's means resourcetype and index? 
"""


class PublicClientPool(ManagedPool):
    def __init__(self, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """
        # print(__name__ + str(kwds))
        super().__init__(**kwds)
        self.getToken()
        self.poolInfo = None

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
        TOKEN_PATH = pcc['cloud_token']

        if os.path.exists(TOKEN_PATH):
            tokenFile = open(TOKEN_PATH, 'r')
            self.token = tokenFile.read()
            tokenFile.close()
            tokenMsg = read_from_cloud('verifyToken', token=self.token)
            if tokenMsg.get('code') != 0:
                os.remove(TOKEN_PATH)
                self.getToken()
        else:
            tokenMsg = read_from_cloud('getToken')
            if tokenMsg['data']:
                tokenFile = open(TOKEN_PATH, 'w+')
                tokenFile.write(tokenMsg['data']['token'])
                tokenFile.close()
                self.token = tokenMsg['data']['token']
            else:
                return tokenMsg['msg']

    def poolExists(self):
        res = read_from_cloud(
            'existPool', poolname=self.poolname, token=self.token)
        if res['msg'] == 'success':
            return True
        else:
            return False

    def restorePool(self):
        res = read_from_cloud(
            'restorePool', poolname=self.poolname, token=self.token)
        if res['msg'] == 'success':
            return True
        else:
            return False

    def createPool(self):
        res = read_from_cloud(
            'createPool', poolname=self.poolname, token=self.token)

        if res['msg'] == 'success':
            return True
        elif res['msg'] == 'The storage pool already exists. Change the storage pool name':
            return True
        elif res['msg'] == 'The storage pool name already exists in the recycle bin. Change the storage pool name':
            raise ValueError(
                res['msg'] + ', please restore pool ' + self.poolname + ' firstly.')
        else:
            return False

    def getPoolInfo(self):
        """
        data:. See productpool::ManagedPool::saveOne
            poolname : 
                _classes= {productTypeName: {currentSn:csn, sn=[]}}
                _urns= [{urn: tags[]}]
                _tags= {urns:[]}
        """
        res = read_from_cloud(
            'infoPool', poolpath=self.poolname, token=self.token)
        if res['code'] == 0:
            if res['data']:
                self.poolInfo = res['data']
                return self.poolInfo
            else:
                return 'No data in the pool ' + self.poolurl
        else:
            raise ValueError(res['msg'])

    def exists(self, urn):
        """
        Determines the existence of a product with specified URN.
        cloud: urn:poolbs:20211018:0,urn:poolbs:20211018:1
        """
        res = read_from_cloud('infoUrn', urn=urn, token=self.token)
        if res['code'] == 0:
            return True
        else:
            return False

    def getProductClasses(self):
        """
        Returns all Product classes found in this pool.
        mh: returns an iterator.
        """
        classes = []
        try:
            if self.poolInfo:
                # for clz in self.poolInfo[self.poolname]['_classes']:
                #    classes.append(clz['productTypeName'])
                pass
            else:
                self.getPoolInfo()
                if self.poolInfo is None:
                    # No such pool in cloud
                    return None
                # for clz in self.poolInfo[self.poolname]['_classes']:
                #    classes.append(clz['productTypeName'])
            classes = list(self.poolInfo[self.poolname]['_classes'])
            return classes
        except TypeError as e:
            raise TypeError(
                'Pool info API changed or unexpected information: ' + str(e))
        except KeyError as e:
            raise TypeError(
                'Pool info API changed or unexpected information: ' + str(e))

    def getCount(self, typename=None):
        """
        Return the number of URNs for the product type.
        """
        try:
            clzes = self.getProductClasses()
            if clzes == 0:
                return 0
            if typename is None:
                return sum(len(td['sn']) for td in self.poolInfo[self.poolname]['_classes'].value())
            if typename not in clzes:
                raise ValueError("Current pool has no such type: " + typename)
            return len(self.poolInfo[self.poolname]['_classes'][typename]['sn'])
        except KeyError:
            return 0

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

    def meta(self, *args, **kwds):
        """
        Loads the meta-data info belonging to the product of specified URN.
        """
        return self.getMetaByUrn(*args, **kwds)

    def getDataType(self):
        res = read_from_cloud('getDataType', token=self.token)
        if res.get('code') == 0:
            return res['data']
        else:
            return []

    def saveOne(self, prd, tag, geturnobjs, serialize_in, serialize_out, res, kwds):
        """
                Save one product.

                :res: list of result.
                :serialize_out: if True returns contents in serialized form.
                """
        jsonPrd = prd
        if serialize_in:
            pn = fullname(prd)
            cls = prd.__class__
            jsonPrd = serialize(prd)
        else:
            # prd is json. extract prod name
            # '... "_STID": "Product"}]'
            pn = prd.rsplit('"', 2)[1]
            cls = Class_Look_Up[pn]
            pn = fullname(cls)

        datatype = self.getDataType()
        if pn not in datatype:
            raise ValueError('No such product type in cloud: ' + pn)

        targetPoolpath = self.getPoolpath() + '/' + pn
        poolInfo = read_from_cloud(
            'infoPoolType', poolpath=targetPoolpath, token=self.token)
        if poolInfo['data'].get(targetPoolpath):
            sn = poolInfo['data'][targetPoolpath]['lastIndex'] + 1
        else:
            sn = 0
        # __import__("pdb").set_trace()
        urn = makeUrn(poolname=self._poolname, typename=pn, index=sn)

        try:
            # save prod to cloud
            if serialize_in:
                uploadRes = self.doSave(resourcetype=pn,
                                        index=sn,
                                        data=jsonPrd,
                                        tag=tag,
                                        serialize_in=serialize_in,
                                        serialize_out=serialize_out,
                                        **kwds)

            else:
                uploadRes = self.doSave(resourcetype=pn,
                                        index=sn,
                                        data=prd,
                                        tag=tag,
                                        serialize_in=serialize_in,
                                        serialize_out=serialize_out,
                                        **kwds)
        except ValueError as e:
            msg = 'product ' + urn + ' saving failed.' + str(e) + trbk(e)
            logger.debug(msg)
            raise e

        if uploadRes['msg'] != 'success':
            raise Exception('Upload failed: ' + uploadRes['msg'])
        else:
            urn = uploadRes['data']['urn']

        if geturnobjs:
            if serialize_out:
                # return the URN string.
                res.append(urn)
            else:
                res.append(Urn(urn))
        else:
            # import pdb
            # pdb.set_trace()
            rf = ProductRef(urn=Urn(urn, poolurl=self.poolurl))
            if serialize_out:
                # return without meta
                res.append(rf)
            else:
                # it seems that there is no better way to set meta
                rf._meta = prd.getMeta()
                res.append(rf)

    def schematicSave(self, products, tag=None, geturnobjs=False, serialize_in=True, serialize_out=False, **kwds):
        """ do the scheme-specific saving.

            :serialize_out: if True returns contents in serialized form.
        """
        res = []
        if not self.poolExists():
            # Create pool
            self.createPool()
        if serialize_in:
            alist = issubclass(products.__class__, list)
            if not alist:
                prd = products
                self.saveOne(prd, tag, geturnobjs,
                             serialize_in, serialize_out, res, kwds)
            else:
                for prd in products:
                    self.saveOne(prd, tag, geturnobjs,
                                 serialize_in, serialize_out, res, kwds)
        else:
            alist = products.lstrip().startswith('[')
            if not alist:
                prd = products
                self.saveOne(prd, tag, geturnobjs,
                             serialize_in, serialize_out, res, kwds)
            else:
                # parse '[ size1, prd, size2, prd2, ...]'

                last_end = 1
                productlist = []
                comma = products.find(',', last_end)
                while comma > 0:
                    length = int(products[last_end: comma])
                    productlist.append(length)
                    last_end = comma + 1 + length
                    prd = products[comma + 2: last_end + 1]
                    self.saveOne(prd, tag, geturnobjs,
                                 serialize_in, serialize_out, res, kwds)
                    # +2 to skip the following ', '
                    last_end += 2
                    comma = products.find(',', last_end)
        # XXX refresh currentSn on server
        self.getPoolInfo()
        sz = 1 if not alist else len(
            products) if serialize_in else len(productlist)
        logger.debug('%d product(s) generated %d %s: %s.' %
                     (sz, len(res), 'Urns ' if geturnobjs else 'prodRefs', lls(res, 200)))

        if alist:
            return serialize(res) if serialize_out else res
        else:
            return serialize(res[0]) if serialize_out else res[0]

    def schematicLoad(self, resourcetype, index, start=None, end=None,
                      serialize_out=False):
        """ do the scheme-specific loading
        """
        targetPoolpath = self.getPoolpath() + '/' + resourcetype
        poolInfo = read_from_cloud(
            'infoPoolType', poolpath=targetPoolpath, token=self.token)
        try:
            if poolInfo['data']:
                poolInfo = poolInfo['data']
                if poolInfo.get(targetPoolpath):
                    if index in poolInfo[targetPoolpath]['indexes']:
                        urn = makeUrn(poolname=self._poolname,
                                      typename=resourcetype, index=index)
                        res = self.doLoadByUrn(urn)
                        # res is a product like fdi.dataset.product.Product

                        if issubclass(res.__class__, BaseProduct):
                            if serialize_out:
                                from fdi.dataset.deserialize import serialize
                                return serialize(res)
                            else:
                                return res
                        else:
                            raise Exception('Load failed: ' + res['msg'])
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

    def doLoadByUrn(self, urn):
        # import pdb
        # pdb.set_trace()
        res = load_from_cloud('pullProduct', token=self.token, urn=urn)
        return res

    def doSave(self, resourcetype, index, data, tag=None, serialize_in=True, **kwds):
        path = self._cloudpoolpath + '/' + resourcetype
        res = load_from_cloud('uploadProduct', token=self.token,
                              products=data, path=path, tags=tag, resourcetype=resourcetype)
        return res

    def schematicRemove(self, urn=None, resourcetype=None, index=None):
        """ do the scheme-specific removing
        """
        prod = resourcetype
        sn = index
        if self.exists(urn):
            try:
                if resourcetype and index:
                    self.doRemove(resourcetype=prod, index=sn)
                else:
                    poolname, resourcetype, index = parseUrn(urn)
                    if self.poolname == poolname:
                        self.doRemove(resourcetype=resourcetype, index=index)
                    else:
                        raise ValueError('You can not delete from pool:' + poolname
                                         + ', because current pool is' + self.poolname)
            except Exception as e:
                msg = 'product ' + urn + ' removal failed'
                logger.debug(msg)
                raise e
        return 0

    def doRemove(self, resourcetype, index):
        """ to be implemented by subclasses to do the action of reemoving
        """
        path = self._cloudpoolpath + '/' + resourcetype + '/' + str(index)
        res = read_from_cloud('remove', token=self.token, path=path)
        print("index: " + str(index) + " remove result: " +
              str(res) + ' from : ' + path)
        return res['msg']

    def remove(self, urn):
        poolname, resource, index = parseUrn(urn)
        return self.doRemove(resource, index)

    def schematicWipe(self):
        self.doWipe()

    def doWipe(self):
        """ to be implemented by subclasses to do the action of wiping.
        """
        # res = read_from_cloud('wipePool', poolname=self.poolname, token=self.token)
        # if res['msg'] != 'success':
        #     raise ValueError('Wipe pool ' + self.poolname + ' failed: ' + res['msg'])
        info = self.getPoolInfo()
        if isinstance(info, dict):
            for clazz, cld in info[self.poolname]['_classes'].items():
                for i in cld['sn']:
                    urn = 'urn:' + self.poolname + ':' + clazz + ':' + str(i)
                    res = self.remove(urn)
                    assert res in ['Not found resource.', 'success']
        else:
            raise ValueError("Update pool information failed: " + str(info))

    def setTag(self, tag, urn):
        """ Set given tag or list of tags to the URN.

        Parameters
        ----------
        :tag: tag or list of tags.
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        if not self.exists(urn):
            raise ValueError('Urn does not exists!')
        if isinstance(tag, (list, str)) and len(tag) > 0:
            t = ', '.join(tag) if isinstance(tag, list) else tag
            res = read_from_cloud('addTag', token=self.token, tags=t, urn=u)
            if res['msg'] != 'OK':
                raise ValueError('Set tag to ' + urn +
                                 ' failed: ' + res['msg'])
        else:
            raise ValueError('Tag can not be empty or non-string!')

    def getTags(self, urn=None):
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        res = read_from_cloud('infoUrn', urn=u, token=self.token)
        if res['code'] == 0:
            ts = [t.split(',') for t in res['data'][u]['tags']]
            return [x.strip() for x in chain(*ts)]
        else:
            raise ValueError('Read tags failed due to : ' + res['msg'])

    def removeTagByUrn(self, tag, urn):
        pass

    def removeTag(self, tag):
        if isinstance(tag, str):
            res = delete_from_server('delTag', token=self.token, tag=tag)
        else:
            raise ValueError('Tag must be a string!')

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


def genProduct(size=1):
    res = []
    for i in range(size):
        x = Product(description="product example with several datasets",
                    instrument="Crystal-Ball", modelName="Mk II", creator='Cloud FDI developer')
        i0 = i
        i1 = [[i0, 2, 3], [4, 5, 6], [7, 8, 9]]
        i2 = 'ev'  # unit
        i3 = 'image1'  # description
        image = ArrayDataset(data=i1, unit=i2, description=i3)
        # put the dataset into the product
        x["RawImage"] = image
        x.set('QualityImage', ArrayDataset(
            [[0.1, 0.5, 0.7], [4e3, 6e7, 8], [-2, 0, 3.1]]))
        res.append(x)
    if size == 1:
        return res[0]
    else:
        return res


# from fdi.pal.query import MetaQuery
# qt = MetaQuery(Product, 'm["extra"] > 5000 and m["extra"] <= 5005')
# <MetaQuery where='m["extra"] > 5000 and m["extra"] <= 5005', type=<class 'fdi.dataset.product.Product'>, variable='m', allVersions=False>

def test_getToken():
    poolurl = 'csdb:///poolbs'
    test_pool = PublicClientPool(poolurl=poolurl)
    tokenFile = open(pcc['cloud_token'], 'r')
    token = tokenFile.read()
    tokenFile.close()
    assert token == test_pool.token, "Tokens are not equal or not synchronized"


def test_poolInfo():
    poolurl = 'csdb:///csdb_test_pool'
    test_pool = PublicClientPool(poolurl=poolurl)
    test_pool.getPoolInfo()
    import pdb
    pdb.set_trace()
    print(test_pool.poolInfo)

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
