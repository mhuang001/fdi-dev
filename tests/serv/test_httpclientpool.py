# -*- coding: utf-8 -*-


from fdi.dataset.product import Product
from fdi.dataset.numericparameter import NumericParameter
from fdi.dataset.stringparameter import StringParameter
from fdi.dataset.eq import deepcmp
from fdi.dataset.deserialize import serialize_args, deserialize_args
from fdi.dataset.testproducts import get_demo_product, get_related_product
from fdi.pal.productstorage import ProductStorage
from fdi.pal.productref import ProductRef
from fdi.pal.publicclientpool import PublicClientPool
from fdi.pal.query import MetaQuery
from fdi.pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
from fdi.pal.httpclientpool import HttpClientPool
from fdi.pns.fdi_requests import *
from fdi.utils.getconfig import getConfig
from fdi.utils.common import fullname

import pytest
import urllib
import getpass
import sys


def setuplogging():
    import logging
    import logging.config
    from . import logdict

    # create logger
    logging.config.dictConfig(logdict.logdict)
    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("filelock").setLevel(logging.WARN)
    return logging


logging = setuplogging()
logger = logging.getLogger()

logger.setLevel(logging.INFO)
logger.debug('logging level %d' % (logger.getEffectiveLevel()))

test_poolid = __name__.replace('.', '_')


@pytest.fixture(scope="module")
def init_test():
    pass


def chksa(a, k):
    p = 0
    for not_quoted in [False, True]:
        s = serialize_args(*a, **k)
        if p:
            print('s= ', s)
        code, a1, k1 = deserialize_args(s, not_quoted=False)
        assert code == 200
        assert a == a1
        assert k == k1
        s = urllib.parse.unquote(s)
        if p:
            print('S= ', s)
        code, a1, k1 = deserialize_args(s, not_quoted=True)
        assert code == 200
        assert a == a1
        assert k == k1


def test_serialize_args():
    a = ['__foo__', 1, 2, -3, 4.0, 'a', 'b c__d', b'\xde\xad',
         True, None, NumericParameter(42)]
    k = {'__f__': '__g__', 'a': 'r', 'f': 0, 'b': True,
         'k': None, 's': StringParameter('4..2')}
    chksa(a, k)
    a = [[1]]
    k = {}
    chksa(a, k)
    a = []
    k = {'s': 2}
    chksa(a, k)
    a, k = ['__foo', {'3': 4}], dict(d=6)
    chksa(a, k)


def test_gen_url2(server):
    aburl, headers = server


def test_gen_url(server):
    """ Makesure that request create corrent url
    """

    aburl, headers = server
    samplepoolname = 'sample_' + test_poolid
    samplepoolurl = aburl + '/' + samplepoolname
    sampleurn = 'urn:' + samplepoolname + ':fdi.dataset.product.Product:10'

    logger.info('Test GET HK')
    got_hk_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='housekeeping', method='GET')
    hk_url = aburl + '/' + samplepoolname + '/hk/'
    assert got_hk_url == hk_url, 'Housekeeping url error: ' + got_hk_url + ':' + hk_url

    logger.info('Test GET classes, urns, tags, webapi url')
    got_classes_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='classes', method='GET')
    classes_url = aburl + '/' + samplepoolname + '/hk/classes'
    assert got_classes_url == classes_url, 'Classes url error: ' + got_classes_url

    got_urns_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='urns', method='GET')
    urns_url = aburl + '/' + samplepoolname + '/hk/urns'
    assert got_urns_url == urns_url, 'Urns url error: ' + got_urns_url

    got_tags_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='tags', method='GET')
    tags_url = aburl + '/' + samplepoolname + '/hk/tags'
    assert got_tags_url == tags_url, 'Housekeeping url error: ' + got_tags_url

    logger.info('Get product url')
    got_product_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='product', method='GET')
    product_url = aburl + '/' + samplepoolname + '/fdi.dataset.product.Product/10'
    assert got_product_url == product_url, 'Get product url error: ' + got_product_url

    logger.info('GET WebAPI  url')
    call = 'tagExists__foo'
    got_webapi_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents=call, method='GET')
    webapi_url = aburl + '/' + samplepoolname + '/' + 'api/' + call
    # '/'
    assert got_webapi_url == webapi_url + '/', 'Get WebAPI url error: ' + got_webapi_url

    logger.info('Post product url')
    got_post_product_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='product', method='POST')
    post_product_url = aburl + '/' + samplepoolname + '/'
    assert got_post_product_url == post_product_url, 'Post product url error: ' + \
                                                     got_post_product_url

    logger.info('Delete product url')
    got_del_product_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='product', method='DELETE')
    del_product_url = aburl + '/urn' + sampleurn
    assert got_del_product_url == del_product_url, 'Delete product url error: ' + \
                                                   got_del_product_url

    logger.info('Delete pool url')
    got_del_pool_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='wipe_pool', method='DELETE')
    del_pool_url = aburl + '/' + samplepoolname + '/wipe'
    assert got_del_pool_url == del_pool_url, 'Delete product url error: ' + got_del_pool_url

    logger.info('Test corrupt request url')
    with pytest.raises(ValueError) as exc:
        err_url = urn2fdiurl(
            urn=sampleurn, poolurl=samplepoolurl, contents='pool', method='GET')
        exc_msg = exc.value.args[0]
        assert exc_msg == 'No such method and contents composition: GET/pool'


def test_CRUD_product_by_client(server, local_pools_dir):
    """Client http product storage READ, CREATE, DELETE products in remote
    """
    aburl, headers = server

    poolid = test_poolid
    poolurl = aburl + '/' + poolid
    pool = HttpClientPool(poolname=poolid, poolurl=poolurl)
    crud_t(poolid, poolurl, local_pools_dir, pool)


def crud_t(poolid, poolurl, local_pools_dir, pool):
    logger.info('Init a pstore')

    if PoolManager.isLoaded(DEFAULT_MEM_POOL):
        PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
    # this will also register the server side
    pstore = ProductStorage(pool=pool)
    pool.removeAll()

    assert len(pstore.getPools()) == 1, 'product storage size error: ' + \
                                        str(pstore.getPools())
    assert pstore.getPool(poolid) is not None, 'Pool ' + \
                                               poolid + ' is None.'

    cnt = pool.getCount('fdi.dataset.product.Product')
    assert cnt == 0, 'Local metadata file size is 2'

    logger.info('Save data by ' + pool.__class__.__name__)
    x = Product(description='desc test')

    urn = pstore.save(x, geturnobjs=True)
    x.creator = 'httpclient'
    urn2 = pstore.save(x, geturnobjs=True)
    typenm = fullname(x)
    expected_urn = 'urn:' + poolid + ':' + fullname(x)
    assert urn.urn.rsplit(':', 1)[0] == expected_urn, \
        'Urn error: ' + expected_urn
    poolpath, scheme, place, pn, un, pw = parse_poolurl(
        poolurl, poolhint=poolid)
    cnt = pool.getCount(typenm)
    assert cnt == 2

    logger.info('Load product from httpclientpool')
    res = pstore.getPool(poolid).loadProduct(urn2.urn)
    assert res.creator == 'httpclient', 'Load product error: ' + str(res)
    diff = deepcmp(x, res)
    assert diff is None, diff

    logger.info('Search metadata')
    q = MetaQuery(Product, 'm["creator"] == "httpclient"')
    res = pstore.select(q)
    assert len(res) == 1, 'Select from metadata error: ' + str(res)

    logger.info('Delete a product from httpclientpool')
    pstore.getPool(poolid).remove(urn.urn)
    lsn = pstore.getPool(poolid).getCount('fdi.dataset.product.Product')
    assert lsn == 1, 'Delete product local error, len sn : ' + lsn
    logger.info('A load exception message is expected')
    with pytest.raises(NameError):
        res = pstore.getPool(poolid).loadProduct(urn.urn)
    with pytest.raises(NameError):
        res = pstore.getPool(poolid).loadProduct(
            urn.urn.replace('Product', 'this_and_the_last_errors.are.expected'))

    logger.info('Wipe a pool')
    pstore.getPool(poolid).removeAll()
    assert pool.isEmpty()

    tag = '==== Demo Product ===='
    logger.info('test sample demo prod with tag: ' + tag)
    sp = get_demo_product()
    sp.refs['a_ref'] = ProductRef(get_related_product())

    urn = pstore.save(sp, tag=tag)
    print('Sample Prod saved with tag "%s" %s to %s' %
          (tag, urn.urn, pool.poolname))

    logger.info('unregister a pool')
    assert len(pstore.getPools()) == 1, 'product storage size error: ' + \
                                        str(pstore.getPools())
    # unregister locally and remotely
    pstore.unregister(poolid)
    assert len(pstore.getPools()) == 0, 'product storage size error: ' + \
                                        str(pstore.getPools())

    logger.info('Access a non-existing pool and trgger an Error.')
    with pytest.raises(NameError):
        pstore.getPool(poolid + 'NON_EXISTS ') is None


def make_pools(name, aburl, n=1):
    """ generate n pools """

    lst = []
    for i in range(n):
        poolid = name + str(n)
        pool = PoolManager.getPool(poolid, aburl + '/' + poolid)
        lst.append(pool)
        ps = ProductStorage(pool).save(Product('lone prod in ' + poolid))
    return lst[0] if n == 1 else lst


def est_Product_path_client(server, local_pools_dir):
    """
    """
    aburl, headers = server

    logger.info('Create pools on the server.')
    poolid = test_poolid
    poolurl = aburl + '/' + poolid
    pool = HttpClientPool(poolname=poolid, poolurl=poolurl)

    if PoolManager.isLoaded(DEFAULT_MEM_POOL):
        PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
    # this will also register the server side
    pstore = ProductStorage(pool=pool)

    x = Product(description='desc test')
    urn = pstore.save(x, geturnobjs=True)
    pool1 = HttpClientPool(poolname=poolid + 'x', poolurl=poolurl + 'x')
    pstore.register(pool=pool1)

    logger.info('Delete all pools on the server.')


from fdi.dataset.arraydataset import ArrayDataset

# ----------------------TEST CSDB--------------------------------
csdb_pool_id = 'csdb_test_pool'


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


@pytest.fixture(scope="module")
def csdb(pc):
    url = pc['cloud_scheme'] + ':///' + csdb_pool_id
    # pc['cloud_host'] + ':' + \
    # str(pc['cloud_port'])
    test_pool = PublicClientPool(poolurl=url)
    return test_pool, url


@pytest.fixture(scope="module")
def test_token(csdb):
    test_pool, url = csdb
    test_pool.getPoolInfo()
    tokenFile = open(pcc['cloud_token'], 'r')
    token = tokenFile.read()
    tokenFile.close()
    assert token == test_pool.token, "Tokens are not equal or not synchronized"
    return token


def test_createPool(csdb):
    test_pool, url = csdb
    try:
        assert test_pool.createPool() == True
    except ValueError:
        assert test_pool.restorePool() == True


def test_poolExists(csdb):
    test_pool, url = csdb
    assert test_pool.poolExists() == True


def test_poolInfo(csdb):
    test_pool, url = csdb
    test_pool.getPoolInfo()
    print(test_pool.poolInfo)


def test_upload():
    poolurl = 'csdb:///' + csdb_pool_id
    poolname = csdb_pool_id

    pstore = ProductStorage(poolname=poolname, poolurl=poolurl)
    test_pool = pstore.getPool(poolname)
    # PoolManager.getPool(poolurl=urnobj.getScheme() + ':///' + urnobj.getPool())

    prd = genProduct()
    res = pstore.save(prd)
    # urn:poolbs:fdi.dataset.product.Product:x
    assert res.urn.startswith('urn:' + csdb_pool_id + ':fdi.dataset.product.Product')


def test_load(csdb):
    test_pool, url = csdb
    prd = test_pool.schematicLoad('fdi.dataset.product.Product', 2)
    assert prd.description == 'product example with several datasets', 'retrieve production incorrect'
    assert prd.instrument == 'Crystal-Ball', 'retrieve production incorrect'
    assert prd['QualityImage'].shape == (3, 3), 'retrieve production incorrect'


def test_add_tag(csdb):
    test_pool, url = csdb
    tag = 'testprd'
    urn = 'urn:' + csdb_pool_id + ':fdi.dataset.product.Product:2'
    test_pool.setTag(tag, urn)
    assert tag in test_pool.getTags(urn)


def test_count(csdb):
    test_pool, url = csdb
    test_pool.setPoolurl('csdb:///' + csdb_pool_id + '/fdi.dataset.product.Product')
    count = test_pool.getCount('/' + csdb_pool_id + '/fdi.dataset.product.Product')
    assert count == 2


def test_remove(csdb):
    test_pool, url = csdb
    urn = 'urn:' + csdb_pool_id + ':fdi.dataset.product.Product:1'
    res = test_pool.remove(urn)
    assert res == 'success', res


def test_wipe(csdb):
    """
    Waiting for /info update, will be failed due to:
    Wipe will check the poolInfo, and poolInfo requires poolurl like: /csdb_test_pool/fdi.dataset.product.Product
    In doRemove(self, resourcetype, index) function, /delete requires a path, the path = self.poolurl + resourcetypes
    Thus, the path = delete?path=/csdb_test_pool/fdi.dataset.product.Product/fdi.dataset.product.Product/2
    """
    test_pool, url = csdb
    test_pool.setPoolurl('csdb:///' + csdb_pool_id + '/fdi.dataset.product.Product')
    test_pool.schematicWipe()


def test_deletePool(csdb):
    test_pool, url = csdb
    assert test_pool.schematicWipe() is None, 'Delete test pool'