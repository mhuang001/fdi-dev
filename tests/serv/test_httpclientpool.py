# -*- coding: utf-8 -*-

from fdi.dataset.deserialize import deserialize
from conftest import SHORT

from test_pal import backup_restore
from serv.test_httppool import getPayload, check_response

from fdi.dataset.product import Product
from fdi.dataset.numericparameter import NumericParameter
from fdi.dataset.stringparameter import StringParameter
from fdi.dataset.eq import deepcmp

from fdi.dataset.deserialize import serialize_args, deserialize_args, deserialize
from fdi.dataset.testproducts import get_demo_product, get_related_product
from fdi.pal.productstorage import ProductStorage
from fdi.pal.productref import ProductRef
from fdi.pal.query import MetaQuery
from fdi.pal.poolmanager import PoolManager, DEFAULT_MEM_POOL
from fdi.pal.httpclientpool import HttpClientPool
from fdi.pns.fdi_requests import safe_client, urn2fdiurl, parse_poolurl
from fdi.utils.common import fullname

import networkx as nx

from flask_httpauth import HTTPBasicAuth
# from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError
import pytest
import os
import json
import time
import urllib
import copy
import time


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
    assert got_webapi_url == webapi_url + \
        '/', 'Get WebAPI url error: ' + got_webapi_url

    logger.info('Post WebAPI url')
    call = 'tagExists__foo'
    got_post_api_url = urn2fdiurl(
        urn=sampleurn, poolurl=samplepoolurl, contents=call, method='POST')
    post_api_url = aburl + '/' + samplepoolname+'/' + 'api/' + 'tagExists/'
    assert got_post_api_url == post_api_url, 'Post WebAPI url error: ' + \
        got_post_api_url

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


def test_tmp_remote_storage(tmp_remote_storage, tmp_prods):

    ps = tmp_remote_storage
    # lit of poolnames
    plst = list(ps.getPools())
    assert len(plst) == 1
    assert plst[0] == 'test_remote_pool'
    pool = ps.getPool(plst[0])

    # empty
    assert pool.getCount() == 0
    assert pool.isEmpty()
    prod_lst = tmp_prods
    refs = []
    for i, p in enumerate(prod_lst):
        ts = 'saved at %d' % time.time_ns()
        refs.append(ps.save(p, tag=ts))
    retrd = []
    for r in refs:
        p = r.product
        retrd.append(p)
        assert p.description.startswith('test-product-')
    assert len(prod_lst) == len(retrd) == pool.getCount()


def est_CRUD_product_by_client(server, local_pools_dir, auth):
    """Client http product storage READ, CREATE, DELETE products in remote
    """
    aburl, headers = server
    client = None
    poolid = test_poolid
    poolurl = aburl + '/' + poolid
    pool = HttpClientPool(poolname=poolid, poolurl=poolurl)
    crud_t(poolid, poolurl, pool, auth, client)


@pytest.fixture(scope=SHORT)
def get_PS_for_CRUD(server, tmp_remote_storage, auth, client):

    logger.info('Init a pstore')

    ps_remote = tmp_remote_storage
    aburl, headers = server
    poolid = ps_remote.getPools()[0]
    pool = ps_remote.getPool(poolid)
    poolurl = pool.poolurl
    if 1:
        if PoolManager.isLoaded(DEFAULT_MEM_POOL):
            PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
    # this will also register the server side
    pstore = ProductStorage(pool=pool, auth=auth, client=client)
    pstore.register(poolid)
    pool.removeAll()

    assert len(pstore.getPools()) == 1, 'product storage size error: ' + \
                                        str(pstore.getPools())
    assert pstore.getPool(poolid) is not None, 'Pool ' + \
                                               poolid + ' is None.'
    return poolid, poolurl, pool, auth, client, pstore


def test_CRUD_product_by_client(get_PS_for_CRUD):
    """Client http product storage READ, CREATE, DELETE products in remote
    """
    logger.info('start CRUD test')

    poolid, poolurl, pool, auth, client, pstore = get_PS_for_CRUD

    cnt = pool.getCount('fdi.dataset.product.Product')
    assert cnt == 0, 'Local metadata file size is 0'
    assert pool.count == 0

    logger.info('Save data by ' + pool.__class__.__name__)
    x = Product(description='desc test')

    urn = pstore.save(x, geturnobjs=True)
    x.creator = 'httpclient'

    urn2 = pstore.save(x, geturnobjs=True)
    typenm = fullname(x)
    expected_urn = 'urn:' + poolid + ':' + fullname(x)
    assert urn.urn.rsplit(':', 1)[0] == expected_urn, \
        'Urn error: ' + expected_urn
    logger.info('Saved two products.')

    poolpath, scheme, place, pn, un, pw = parse_poolurl(
        poolurl, poolhint=poolid)
    # import http
    # http.client.HTTPConnection.debuglevel = 1

    cnt = pool.getCount(typenm)
    assert cnt == pool.getCount()

    assert cnt == 2 == pool.count

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
    try:
        assert pool.isEmpty()
        assert pool.count == 0
    except ConnectionError:
        logger.info('Unregistered Pool raises connectionError.')
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


def est_webapi_backup_restore(server):
    """
    """
    aburl, headers = server

    logger.info('Create pools on the server.')
    poolid = test_poolid
    poolurl = aburl + '/' + poolid
    pool = HttpClientPool(poolname=poolid, poolurl=poolurl)

    logger.info('Bacckup/restore a pool on the server.')

    if PoolManager.isLoaded(DEFAULT_MEM_POOL):
        PoolManager.getPool(DEFAULT_MEM_POOL).removeAll()
    # this will also register the server side
    pstore = ProductStorage(pool=pool)
    backup_restore(pstore)


def test_webapi_backup_restore(tmp_remote_storage):
    """
    """
    logger.info('Create pools on the server.')
    pstore = tmp_remote_storage
    logger.info('Bacckup/restore a pool on the server.')
    backup_restore(pstore)


def test_flask_fmt(tmp_pools, server, client,  auth):
    pool, prd, ref, tag = tmp_pools[0]
    aburl, header = server
    prd_urn = ref.urn

    #### /{pool}  /{pool}/  GET  ####

    # server url without slash
    aburl_no_slash = aburl.rstrip('/')
    # get poolname
    x = safe_client(client.get, aburl_no_slash, auth=auth)
    o, code = getPayload(x)
    # check to see if the pool url is malformed
    check_response(o, code=code, failed_case=False)
    # should be a list of names
    poolnames = o['result']
    assert isinstance(poolnames, dict)
    assert pool._poolname in poolnames

    # check to see if the pool url is malformed by checking if
    # the pool's url can be used to retrieve the pool
    from fdi.pal.urn import Urn, parseUrn
    p_pname, p_type, p_index = parseUrn(prd_urn)

    received_poolurls_no_slash = poolnames[pool._poolname].rstrip('/')
    # get pool with products and their urls

    x = safe_client(client.get, received_poolurls_no_slash, auth=auth)
    o, code = getPayload(x)
    # check to see if the pool url is malformed
    check_response(o, code=code, failed_case=False)
    # The product under the correct type and sn has the right tag
    # tags are a string to make btter display.

    # the url is right
    assert o['result']['DataTypes'][p_type][p_index]['url'] == '/'.join(
        (received_poolurls_no_slash, p_type, str(p_index)))
    assert o['result']['DataTypes'][p_type][p_index]['tags'] == str([tag])
    # pool aburl with slash
    # get the pool using url with slash
    received_poolurls_slash = received_poolurls_no_slash+'/'
    x1 = safe_client(client.get, received_poolurls_slash, auth=auth)
    o1, code = getPayload(x1)
    assert o['result'] == o1['result']

    aburl_slash = aburl_no_slash+'/'
    x = safe_client(client.get, aburl_slash, auth=auth)
    o, code = getPayload(x)
    check_response(o, code=code, failed_case=False)
    # should be a list of names
    poolnames = o['result']
    assert isinstance(poolnames, list)
    assert pool._poolname in poolnames


def test_slash(tmp_remote_storage, tmp_prods):
    # add urn
    ps = tmp_remote_storage
    p0_, p11_, p12_, p121, p122, p1221, p12211 = tmp_prods
    urn12211 = ps.save(p12211).urn


def test_hist(tmp_remote_storage, tmp_prods):
    # add urn
    ps = tmp_remote_storage
    p0_, p11_, p12_, p121, p122, p1221, p12211 = tmp_prods
    urn12211 = ps.save(p12211).urn
    p1221.history.add_input(refs={'p1-2-2-1-1': urn12211})
    assert p1221.history.rowCount == 1
    assert p12211.history.rowCount == 0

    urn1221 = ps.save(p1221).urn
    p122.history.add_input(refs={'p1-2-2-1': urn1221})
    assert p121.history.rowCount == 0
    assert p122.history.rowCount == 1

    # get fresh p0, p11, p12 in case they used for something else
    p11 = copy.deepcopy(p11_)
    p12 = copy.deepcopy(p12_)

    urn121 = ps.save(p121).urn
    urn122 = ps.save(p122).urn
    p12.history.add_input(refs={'p1-2-1': urn121, 'p1-2-2': urn122})
    assert p11.history.rowCount == 0
    assert p12.history.rowCount == 2

    urn11 = ps.save(p11).urn
    urn12 = ps.save(p12).urn
    p0 = copy.deepcopy(p0_)
    v = p0.history
    v.add_input(refs={'p1-1': urn11, 'p1-2': urn12})
    assert v.rowCount == 2

    # use ref as labels
    th = v.getTaskHistory(use_name=False, verbose=0)
    pdot = nx.drawing.nx_pydot.to_pydot(th)
    print(pdot.to_string())
    assert len(th.nodes) == 7
    assert len(th.adj) == 7
    assert len(list(th.pred['root'])) == 2

    urn0 = ps.save(p0).urn
    h = p0.history.getTaskHistory(verbose=False)
    h.nodes['root']['product_ref'] = f'"{urn0}"'
    if 1:
        assert len(p11.history['name']) == 0
        assert p12.history['name'][0] == 'p1-2-1'
        assert p12.history['name'][1] == 'p1-2-2'
        assert p122.history['name'][0] == 'p1-2-2-1'
        assert p1221.history['name'][0] == 'p1-2-2-1-1'
        assert nx.is_directed_acyclic_graph(h)

    assert len(h.adj) == 7
    pdot = nx.drawing.nx_pydot.to_pydot(h)
    print(pdot.to_string())


def test_no_auth(tmp_pools, server, client):

    pool, prd, ref, tag = tmp_pools[0]
    aburl, header = server
    prd_urn = ref.urn

    # get pool without auth
    x = safe_client(client.get, aburl, auth=None)
    o, code = getPayload(x)
    # check to see if the pool url is malformed
    check_response(o, code=code, failed_case=False)
    # pool name is found
    assert pool.poolname in o['result']


def test_need_auth(existing_pools, server, client, auth):
    pool = existing_pools[0]
    aburl, header = server

    url = '/'.join((aburl, pool.poolname, 'hk/'))
    # get pool with auth
    x = safe_client(client.get, url, auth=auth)
    cookie = x.cookies
    o, code = getPayload(x)

    # check to see if the pool url is malformed
    check_response(o, code=code, failed_case=False)
    assert o['msg'] == 'OK.'

    # in session
    url = '/'.join((aburl, pool.poolname, 'hk/dTags'))

    x = safe_client(client.get, url, auth=auth)

    o, code = getPayload(x)
    check_response(o, code=code, failed_case=False)
    assert o['msg'] == 'dTags HK data returned OK'
