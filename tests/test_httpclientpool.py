
import pytest
import sys
import base64
from urllib.request import pathname2url
from requests.auth import HTTPBasicAuth
import requests
import random
import os
import pkg_resources
import copy
import time


from fdi.dataset.product import Product
from fdi.dataset.metadata import Parameter, NumericParameter, MetaData
from fdi.dataset.finetime import FineTime1, utcobj
from fdi.dataset.dataset import ArrayDataset, TableDataset, Column
from fdi.dataset.eq import deepcmp
from fdi.pal.context import Context, MapContext
from fdi.pal.productref import ProductRef
from fdi.pal.query import MetaQuery
from fdi.pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
from fdi.pal.productstorage import ProductStorage
from fdi.pal.httpclientpool import HttpClientPool, HttpClientPool2
from fdi.pns.pnsconfig import pnsconfig as pcc
from fdi.pns.fdi_requests import *
from fdi.dataset.odict import ODict
from fdi.utils.getconfig import getConfig
from fdi.utils.common import fullname


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


logger = logging.getLogger()


pcc.update(getConfig())
logger.setLevel(logging.INFO)
setuplogging()
logger.debug('logging level %d' % (logger.getEffectiveLevel()))


test_poolid = 'client_test_pool'


@pytest.fixture(scope="module")
def init_test():
    pass


def test_gen_url():
    """ Makesure that request create corrent url
    """
    samplepoolname = 'defaultpool'
    samplepoolurl = 'http://127.0.0.1:8080/v0.6/' + samplepoolname
    sampleurn = 'urn:' + samplepoolname + ':fdi.dataset.product.Product:10'

    logger.info('Test GET HK')
    base = pcc['baseurl']
    got_hk_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='housekeeping', method='GET')
    hk_url = 'http://127.0.0.1:8080' + \
        base + '/defaultpool/hk'
    assert got_hk_url == hk_url, 'Housekeeping url error: ' + got_hk_url + ':' + hk_url

    logger.info('Test GET classes, urns, tags url')
    got_classes_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='classes', method='GET')
    classes_url = 'http://127.0.0.1:8080' + \
        base + '/defaultpool/hk/classes'
    assert got_classes_url == classes_url, 'Classes url error: ' + got_classes_url

    got_urns_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='urns', method='GET')
    urns_url = 'http://127.0.0.1:8080' + \
        base + '/defaultpool/hk/urns'
    assert got_urns_url == urns_url, 'Urns url error: ' + got_urns_url

    got_tags_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='tags', method='GET')
    tags_url = 'http://127.0.0.1:8080' + \
        base + '/defaultpool/hk/tags'
    assert got_tags_url == tags_url, 'Housekeeping url error: ' + got_tags_url

    logger.info('Get product url')
    got_product_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='product', method='GET')
    product_url = 'http://127.0.0.1:8080' + \
        base + \
        '/defaultpool/fdi.dataset.product.Product/10'
    assert got_product_url == product_url, 'Get product url error: ' + got_product_url

    logger.info('Post product url')
    got_post_product_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='product', method='POST')
    post_product_url = 'http://127.0.0.1:8080' + \
        base + \
        '/defaultpool/fdi.dataset.product.Product/10'
    assert got_post_product_url == post_product_url, 'Post product url error: ' + \
        got_post_product_url

    logger.info('Delete product url')
    got_del_product_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='product', method='DELETE')
    del_product_url = 'http://127.0.0.1:8080' + \
        base + \
        '/defaultpool/fdi.dataset.product.Product/10'
    assert got_del_product_url == del_product_url, 'Delete product url error: ' + \
        got_del_product_url

    logger.info('Delete pool url')
    got_del_pool_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents='pool', method='DELETE')
    del_pool_url = 'http://127.0.0.1:8080' + \
        base + '/defaultpool'
    assert got_del_pool_url == del_pool_url, 'Delete product url error: ' + got_del_pool_url

    logger.info('Test corrupt request url')
    with pytest.raises(ValueError) as exc:
        err_url = urn2fdiurl(
            urn=sampleurn, poolurl=samplepoolurl, contents='pool', method='GET')
        exc_msg = exc.value.args[0]
        assert exc_msg == 'No such method and contents composition: GET/pool'


def test_CRUD_product_by_client():
    """Client http product storage READ, CREATE, DELETE products in remote
    """

    poolpath = pcc['base_poolpath']
    poolid = test_poolid+'1'
    poolurl = pcc['httphost'] + pcc['baseurl'] + \
        '/' + poolid
    pool = HttpClientPool(poolname=poolid,
                          poolurl=poolurl)
    crud_t(poolid, poolurl, poolpath, pool)

    poolpath = pcc['base_poolpath']
    poolid = test_poolid+'2'
    poolurl = pcc['httphost'] + pcc['baseurl'] + \
        '/' + poolid
    pool = HttpClientPool2(poolname=poolid,
                           poolurl=poolurl, poolpath_local=poolpath)
    crud_t(poolid, poolurl, poolpath, pool)


def crud_t(poolid, poolurl, poolpath_local, pool):
    logger.info('Init a pstore')

    if PoolManager.isLoaded(DEFAULT_MEM_POOL):
        PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
    PoolManager.removeAll()
    pstore = ProductStorage(pool=pool)
    assert len(pstore.getPools()) == 1, 'product storage size error: ' + \
        str(pstore.getPools())
    assert pstore.getPool(poolid) is not None, 'Pool ' + \
        poolid+' is None.'

    logger.info('Save data by httpclientpool')
    x = Product(description='desc test')
    x.creator = 'httpclient'
    urn = pstore.save(x, geturnobjs=True)
    urn2 = pstore.save(x, geturnobjs=True)
    expected_urn = 'urn:' + poolid + ':' + fullname(x)
    assert urn.urn.rsplit(':', 1)[0] == expected_urn, \
        'Urn error: ' + expected_urn
    poolpath, scheme, place, pn = parse_poolurl(
        poolurl, poolhint=poolid)
    if issubclass(pool.__class__, HttpClientPool2):
        real_poolpath = os.path.join(pcc['base_poolpath'], poolid)
        assert os.path.exists(real_poolpath), \
            'local metadata file not found: ' + real_poolpath
        assert len(os.listdir(real_poolpath)) >= 3, \
            'Local metadata file size is less than 3'

    logger.info('Load product from httpclientpool')
    res = pstore.getPool(poolid).loadProduct(urn.urn)
    assert res.creator == 'httpclient', 'Load product error: ' + str(res)
    diff = deepcmp(x, res)
    assert diff is None, diff

    if issubclass(pool.__class__, HttpClientPool2):
        logger.info('Search metadata')
        q = MetaQuery(Product, 'm["creator"] == "httpclient"')
        res = pstore.select(q)
        assert len(res) > 0, 'Select from metadata error: ' + str(res)

    logger.info('Delete a product from httpclientpool')
    pstore.getPool(poolid).remove(urn.urn)
    if issubclass(pool.__class__, HttpClientPool2):
        sn = pstore.getPool(
            poolid)._classes['fdi.dataset.product.Product']['sn']
        assert len(sn) >= 1, 'Delete product local error, sn : ' + str(sn)
        logger.info('A load exception message is expected')

    with pytest.raises(NameError):
        res = pstore.getPool(poolid).loadProduct(urn.urn)

    logger.info('Delete a pool')
    pstore.getPool(poolid).removeAll()
    if issubclass(pool.__class__, HttpClientPool2):
        poolfiles = os.listdir(real_poolpath)
        assert len(
            poolfiles) == 0, 'Delete pool, but local file exists: ' + str(poolfiles)
        reshk = pstore.getPool(poolid).readHK()
        assert reshk[0] == ODict(
        ), 'Server classes is not empty after delete: ' + str(reshk[0])
