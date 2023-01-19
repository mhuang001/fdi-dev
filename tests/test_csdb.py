#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from serv.test_httppool import getPayload, check_response
from fdi.dataset.testproducts import get_demo_product, get_related_product
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.product import Product
from fdi.dataset.dateparameter import DateParameter
from fdi.pal.context import MapContext
from fdi.dataset.arraydataset import ArrayDataset
from fdi.dataset.stringparameter import StringParameter
from fdi.pal.productstorage import ProductStorage
from fdi.dataset.eq import deepcmp
from fdi.pns.jsonio import commonheaders, auth_headers
from fdi.dataset.classes import Classes, Class_Module_Map
from svom.products.projectclasses import PC
from fdi.utils.getconfig import getConfig
from fdi.utils.common import lls
from conftest import csdb_pool_id, SHORT
from fdi.pal.publicclientpool import PublicClientPool
from fdi.utils.getconfig import getConfig

import json
import time
import os
from datetime import datetime
import pytest
import requests
import logging
# create logger

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)8s %(process)d '
                    '%(threadName)s %(levelname)s %(funcName)10s()'
                    '%(lineno)3d- %(message)s')

logger = logging.getLogger(__name__)
logger.debug('logging level %d' % (logger.getEffectiveLevel()))

LOOK_UP = PC.mapping
pc = getConfig()

# -------------------TEST CSDB WITH Requests.session a client -----
# low level and not as complete as the later part.


@pytest.fixture(scope='session')
def csdb_client(urlcsdb):
    urlupload = urlcsdb + '/datatype/upload'
    urldelete = urlcsdb + '/datatype/'
    urllist = urlcsdb + '/datatype/list'
    client = requests.session()
    headers = client.headers
    headers = auth_headers(pc['cloud_username'], pc['cloud_password'],
                           headers)
    client.headers.update(headers)
    yield urlupload, urldelete, urllist, client


def get_all_prod_types(urllist, client):
    x = client.get(urllist)
    o, code = getPayload(x)
    types = o['data']
    return types


def add_a_productType(full_name, jsn, client):
    hdr = {"accept": "*/*"}
    fdata = {"file": (full_name, jsn)}
    data = {"metaPath": "/metadata", "productType": full_name}
    urlupload = 'http://123.56.102.90:31702/csdb/v1/datatype/upload'
    x = client.post(urlupload, files=fdata, data=data, headers=hdr)
    return x


def upload_defintion(clsn, full_name, urllist, urlupload, urldelete,
                     asci=True, client=None):
    """upload the definition of given class.

    """
    # new one not there?
    types = get_all_prod_types(urllist, client=client)
    # print(lls(types, 80), full_name in types)
    # delete if exisiting
    if full_name in types:  # and full_name.startswith('sv.'):
        x = client.delete(urldelete+full_name)
        o, code = getPayload(x)
        assert o['data'] is None
        # gone
        types = get_all_prod_types(urllist, client)
    assert full_name not in types

    # upload
    obj = PC.mapping[clsn]()
    jsn = json.dumps(obj.zInfo, ensure_ascii=asci, indent=2)
    # with open(filen, 'w+', encoding='utf-8') as f:
    #     f.write(jsn)
    # with open(filen, 'rb') as f:
    #     fdata = [("file", (filen, f))]
    if 1:
        x = add_a_productType(full_name, jsn=jsn, client=client)
        #### !!!! This throws error !!! ####
        assert x.status_code == 200, x.text
        o, code = getPayload(x)
        assert o['code'] == 0
        assert o['data'] is None

    # check ptypes again
    types = get_all_prod_types(urllist, client)
    # print(types)
    assert full_name in types
    return full_name


USE_SV_MODULE_NAME = False


def test_upload_definition_Tx(csdb_client):
    """ define a prodect and upload the definition """
    urlupload, urldelete, urllist, client = csdb_client

    asci = False

    cls = 'TP'
    if USE_SV_MODULE_NAME:
        cls_full_name = f'sv.{cls}'  # cls_full_name.rsplit('.', 1)[-1]
    else:
        cls_full_name = Class_Module_Map[cls] + '.' + cls
    upload_defintion(cls, cls_full_name, urllist, urlupload, urldelete,
                     asci=True, client=client)


def upload_prod_data(prd, cls_full_name,
                     desc, obj, obs_id, instr, start, end,
                     level='CL1a', program='GRB', url='',
                     client=None, verify=False):
    """ upload product data """

    prd.description = desc
    prd.instrument = StringParameter(instr)
    prd.version = '0.1'
    prd.startDate = DateParameter(start)
    prd.startDate = DateParameter(end)
    prd.meta['object'] = StringParameter(obj)
    prd.meta['obs_id'] = StringParameter(obs_id)
    prd.level = level
    prd.meta['program'] = StringParameter(program)
    jsn = prd.serialized(indent=2)

    if 0:
        filen = f'/cygdrive/d/code/tmp/clz/{cls_full_name}.jsn'
        with open(filen, 'w+', encoding='utf-8') as f:
            f.write(jsn)
        hdr = {"accept": "*/*", 'X-CSDB-METADATA': '/_ATTR_meta'}
        with open(filen, 'rb') as f:
            fdata = [("file", (filen, f))]
    if 1:
        prd = jsn
        fdata = {'file': (cls_full_name, prd)}
        data = {'tags': 'foo,'+str(datetime.now())}
        hdr = {}
        hdr['X-AUTH-TOKEN'] = getattr(client, 'token', '')
        hdr['X-CSDB-AUTOINDEX'] = '1'
        hdr['X-CSDB-METADATA'] = '/_ATTR_meta'
        hdr['X-CSDB-HASHCOMPARE'] = '0'

        # url urlupdata = urlcsdb + f'/storage/{pool}/{cls_full_name}'
        x = client.post(url, files=fdata, data=data, headers=hdr)
        assert x.status_code == 200, lls(x.text, 500)
        o, code = getPayload(x)
        assert o['code'] == 0
        urn = o['data']['urn']
        path = o['data']['path']
        typ = o['data']['type']

        logger.debug("uploaded product urn={urn} path={path} type={typ}")
        """ output example:
            {
              "code": 0,
              "data": {
                "index": 0,
                "md5": "string",
                "path": "string",
                "size": 0,
                "tags": [
                  "string"
                ],
                "timestamp": 0,
                "type": "string",
                "url": "string",
                "urn": "string"
              },
              "msg": "string",
              "total": 0
            }

    Example: 
    url: http://IP:port/csdb/v1/storage/test_csdb_fdi/fdi.dataset.testproducts.TP
     o['data']
     {'index': 424,
     'md5': '2DAFEA60ECC01443DCFE21E23096F98A',
     'path': '/test_csdb_fdi/fdi.dataset.testproducts.TP/424',
     'size': 45394,
     'tags': ['2023-01-15 15:56:38.782800'],
     'timestamp': 1673769399861,
     'type': None,
     'url': 'http://123.56.102.90:31702/csdb/v1/storage/test_csdb_fdi/fdi.dataset.testproducts.TP/424',
     'urn': 'urn:test_csdb_fdi:fdi.dataset.testproducts.TP:424'}

"""
    if verify:
        # read back
        y = client.get(o['data']['url'])
        assert y.text == jsn

    logger.info('Get URN %s' % o['data']['urn'])
    return o['data']


def test_upload_Tx_data(csdb_client, urlcsdb):
    """ upload a demo prod. """

    urlupload, urldelete, urllist, client = csdb_client

    pool = csdb_pool_id
    cls = 'TP'
    if USE_SV_MODULE_NAME:
        cls_full_name = f'sv.{cls}'
    else:
        cls_full_name = Class_Module_Map[cls] + '.' + cls

    urlupdata = urlcsdb + f'/storage/{pool}/{cls_full_name}'
    pdemo = get_demo_product()
    res = upload_prod_data(pdemo,
                           cls_full_name=cls_full_name,
                           desc='Demo_Product',
                           obj='3c273',
                           obs_id='b2000a',
                           instr='VT',
                           start='2000-01-01T00:00:00',
                           end='2001-01-01T00:00:00',
                           level='CL2a',
                           program='PPT',
                           url=urlupdata,
                           client=client,
                           verify=True
                           )
    logger.debug(f'{cls_full_name} uploaded {res}')


def get_all_in_pool(path, what='urn', urlc='', client=None, limit=10000):
    """Return all of something in a pool.

    Parameters
    ----------
    path : str
        '/{poolname}', or '/{poolname}/{product-name}', or
        '/{poolname}/{product-name}/{index.aka.serial-number}',
        e.g. '/sv1/sv.BaseProduct'
    what : str
        which item in ['data'] list to return. e.g. 'urn' means a list
        of URNs found in the path. 'count' means the length of
        ['data'].
    urlc : str
        path to be prepended before `/storage/searcBy...`.
    client : Session
        requets.Session
    limit : str
        how many items per page maximum.

    Returns
    -------
    list or int
        list of `what` or lenth.

    """
    url = urlc + \
        f'/storage/searchByPoolOrPath?limitCount={limit}&path={path}'
    x = client.get(url)
    assert x.status_code == 200
    o, code = getPayload(x)
    assert o['code'] == 0
    prodList = o['data']
    """  "data": [
    {
      "url": "http://123.56.102.90:31702/csdb/v1/storage/sv1/sv.BaseProduct",
      "path": "/sv1/sv.BaseProduct",
      "urn": "urn:sv1:sv.BaseProduct:0",
      "timestamp": 1671773434985,
      "tags": [],
      "index": 0,
      "md5": "217D740304BAB338AD4CB4A52A123864",
      "size": 9854,
      "contentType": null,
      "fileName": "/cygdrive/d/code/tmp/clz/sv.BaseProduct.jsn",
      "productType": "sv.BaseProduct"
    }, ...
    """
    return len(prodList) if what == 'count' else [p[what] for p in prodList]


def pool_exists(poolname, csdb_c, urlc, create_if_not_exists=False):
    urlupload, urldelete, urllist, client = csdb_c

    x = client.get(urlc+f"/pool/info?storagePoolName={poolname}")
    assert x.status_code == 200
    o, code = getPayload(x)
    if o['code'] == 0:
        return True
    elif create_if_not_exists:
        x = client.post(
            urlc+f"/pool/create?poolName={poolname}&read=0&write=0")
        assert x.status_code == 200
        o, code = getPayload(x)
        return o['code'] == 0
    return o['code'] == 0


def test_upload_definition_Product(csdb_client, urlcsdb):
    """ define Product and upload the definition """

    urlupload, urldelete, urllist, client = csdb_client

    pool = urlcsdb + "/pool/create?poolName=sv1&read=0&write=0"

    prds = [p for p in LOOK_UP.values() if issubclass(p.__class__, type) and
            issubclass(p, BaseProduct) and p.__name__ in
            ['Product', 'MapContext']]

    for p in prds:
        cls = p.__name__
        cls_full_name = Class_Module_Map[cls] + '.' + cls
        upload_defintion(cls, cls_full_name,
                         urllist, urlupload, urldelete,
                         asci=True, client=client)
        logger.info(f'Defined {cls_full_name}')


@ pytest.fixture(scope='function')
def upload_7products(csdb, urlcsdb, csdb_client, tmp_prods):

    ftest_pool, poolurl, pstore = csdb
    urlupload, urldelete, urllist, client = csdb_client
    get_all_prod_types(urlcsdb+'/datatype/list', ftest_pool.client)
    # 7 products
    prds = tmp_prods

    # check pool
    pool = csdb_pool_id
    pool_exists(pool, csdb_client, urlcsdb, create_if_not_exists=True)

    all_data = []
    for i, prd in enumerate(prds):
        cls = prd.__class__.__name__
        # make full names
        if USE_SV_MODULE_NAME:
            cls_full_name = f'sv.{cls}'  # cls_full_name.rsplit('.', 1)[-1]
        else:
            cls_full_name = Class_Module_Map[cls] + '.' + cls
        urlupdata = urlcsdb + f'/storage/{pool}/{cls_full_name}'
        all_data.append(upload_prod_data(prd,
                                         cls_full_name=cls_full_name,
                                         desc=f'Demo_{cls}',
                                         obj=cls,
                                         obs_id=f'b2000a_{cls_full_name}',
                                         instr='VT',
                                         start='2000-01-01T00:00:00',
                                         end='2001-01-01T00:00:00',
                                         level='CL2a',
                                         program='PPT',
                                         url=urlupdata,
                                         client=client
                                         )
                        )
    return all_data


def add_a_prod_in_another_pool(poolname2, urlc, cls_full_name, csdb_c):
    path2 = f'{poolname2}/{cls_full_name}'
    urlupdata = urlc + f'/storage/{path2}'
    prd = Classes.mapping[cls_full_name.rsplit('.', 1)[1]]()
    pool_exists(f'{poolname2}', csdb_c, urlc,
                create_if_not_exists=True)
    upload_prod_data(prd,
                     cls_full_name=cls_full_name,
                     desc=f'delte_dataType_control',
                     obj='ctrl',
                     obs_id=f'test_ctrl_{cls_full_name}',
                     instr='VT',
                     start='2000-01-01T00:00:00',
                     end='2001-01-01T00:00:00',
                     level='CL2a',
                     program='PPT',
                     url=urlupdata,
                     client=csdb_c[-1]
                     )
    # number of control prod
    aip_ctl = get_all_in_pool(
        path=f'/{path2}', what='urn', urlc=urlc, client=csdb_c[-1]
    )
    assert all(cls_full_name in a for a in aip_ctl)
    return aip_ctl


def test_del_products(urlcsdb, csdb_client, upload_7products):
    """ delete product data from a pool"""

    urlupload, urldelete, urllist, client = csdb_client
    poolname = csdb_pool_id
    sn = 0
    verify = True
    data = upload_7products

    # 1 for del one peod; 0 for del all of the type
    del1 = 1
    for dt in data:
        # ‘productType' in post storage/pool/prod, None in ['type']
        cls_full_name = dt['path'].rsplit('/', 2)[-2]
        ind = dt['index']
        # number of prod of the ame type
        aip = get_all_in_pool(
            path=f'/{poolname}/{cls_full_name}', what='urn', urlc=urlcsdb, client=client)
        ind = f'/{ind}' if del1 else ''
        # the first urn in aip does not have  ':0' at the end
        _u = dt['urn'][:-2] if dt['urn'].endswith(':0') else dt['urn']

        assert _u in aip
        if del1:  # delete one product
            url = urlcsdb + \
                f"/storage/delete?path=/{poolname}/{cls_full_name}{ind}"
            x = client.post(url)
        else:
            # add a prod in a different pool {pool}2

            aip_ctl = add_a_prod_in_another_pool(
                poolname+'2', urlcsdb, cls_full_name, csdb_client)
            # delete from pool 1
            url = urlcsdb + \
                f"/storage/delDatatype?path=/{poolname}/{cls_full_name}"
            x = client.delete(url)

        assert x.status_code == 200, x.text
        o, code = getPayload(x)
        assert o['code'] == 0, o['msg']
        aip2 = get_all_in_pool(
            path=f'/{poolname}/{cls_full_name}', what='urn', urlc=urlcsdb, client=client)
        if del1:
            assert dt['urn'] not in aip2
            assert len(aip2) == len(aip) - 1
            del1 = 0
        else:
            aip_ctl2 = get_all_in_pool(
                path=f'/{poolname}2/{cls_full_name}', what='urn', urlc=urlcsdb, client=client)
            # control pool not affected
            assert len(aip_ctl) == len(aip_ctl2)
            break


def test_list(csdb_client, urlcsdb):
    """ list all urns in a pool """

    urlupload, urldelete, urllist, client = csdb_client
    allurns = get_all_in_pool(csdb_pool_id, 'urn', urlcsdb, client)
    # logger.info(pformat(allurns))

# ----------------------TEST CSDB WITH ProductStorage----------------


def genProduct(size=1, cls='ArrayDataset', unique='', prod_cls=None):
    res = []
    if prod_cls is None:
        prod_cls = Product
    for i in range(size):
        x = prod_cls(description="product example with several datasets" + unique,
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


def genMapContext(size=1):
    map1 = MapContext(description='product with refs 1')
    map1['creator'] = 'Cloud FDI developer'
    return map1


@ pytest.fixture(scope="session")
def csdb_token(csdb, pc):
    logger.info('test token')
    test_pool, url, pstore = csdb

    token = pc['cloud_token']
    if token != test_pool.token:
        logger.info("Tokens are not equal or not synchronized")
    return token


def test_csdb_token(csdb_token):
    tok = csdb_token


def test_csdb_createPool(csdb_new):
    logger.info('test create a brand new pool')
    test_pool, url, pstore = csdb_new
    try:
        info_of_a_pool = test_pool.poolInfo[test_pool.poolname]
        #assert len(info_of_a_pool['_classes']) == 0
    except ValueError:
        # found deleted pool by this name.
        assert test_pool.restorePool() is True
    assert test_pool.poolExists() is True


def test_csdb_poolInfo(csdb):
    test_pool, url, pstore = csdb
    test_pool.getPoolInfo()
    print(test_pool.poolInfo)


def test_clean_csdb(clean_csdb):
    logger.info('test get classes')
    test_pool, url, pstore = clean_csdb
    pinfo = test_pool.getPoolInfo()
    assert len(pinfo[test_pool.poolname]['_classes'].keys()) == 0
    assert len(pinfo[test_pool.poolname]['_tags'].keys()) == 0
    assert len(pinfo[test_pool.poolname]['_urns'].keys()) == 0
    # __import__("pdb").set_trace()
    pinfo = test_pool.getPoolInfo()

    cls_full_name = 'fdi.dataset.testproducts.TP'
    x = add_a_productType(cls_full_name, jsn=jsn)
    clz = test_pool.getProductClasses()
    assert len(clz) == 0


def test_getProductClasses(urlcsdb, csdb, csdb_client):
    urlupload, urldelete, urllist, client = csdb_client
    test_pool, url, pstore = csdb
    types = get_all_prod_types(urllist, client)
    clz = test_pool.getProductClasses()
    assert len(types)
    assert all(c in types for c in clz)
    # add another prod in pool2
    pool2 = test_pool._poolname + '2'
    cls = 'TC'
    if USE_SV_MODULE_NAME:
        cls_full_name = f'sv.{cls}'
    else:
        cls_full_name = Class_Module_Map[cls] + '.' + cls
    aip_ctl = add_a_prod_in_another_pool(
        pool2, urlcsdb, cls_full_name, csdb_client)

    assert len(aip_ctl) > 0
    assert all(cls_full_name not in c for c in clz)
    assert any(cls_full_name not in c for c in types)
    assert cls_full_name in aip_ctl[-1]


@ pytest.fixture(scope='module')
def csdb_7types_defined(csdb, urlcsdb, csdb_client, tmp_prod_types):

    urlupload, urldelete, urllist, client = csdb_client
    ftest_pool, poolurl, pstore = csdb
    # get_all_prod_types(urlcsdb+'/datatype/list', ftest_pool.client)
    # 7 products
    prd_types = tmp_prod_types

    asci = False

    # check pool
    pool = csdb_pool_id
    pool_exists(pool, csdb_client, urlcsdb, create_if_not_exists=True)
    types = get_all_prod_types(urllist, client)

    all_data = []
    for i, ty in enumerate(prd_types):
        cls = ty.__name__
        # make full names
        if USE_SV_MODULE_NAME:
            cls_full_name = f'sv.{cls}'  # cls_full_name.rsplit('.', 1)[-1]
        else:
            cls_full_name = Class_Module_Map[cls] + '.' + cls

        if cls_full_name not in types:
            defn = upload_defintion(cls, cls_full_name,
                                    urllist, urlupload, urldelete,
                                    asci=True, client=client)
            logger.info(f'Added definition for New Product {cls_full_name}.')
        all_data.append(cls_full_name)
    return all_data


@ pytest.fixture(scope='function')
def csdb_uploaded(csdb, csdb_7types_defined, csdb_client):
    urlupload, urldelete, urllist, client = csdb_client

    test_pool, poolurl, pstore = csdb
    poolname = test_pool._poolname
    __import__("pdb").set_trace()

    all7Types = csdb_7types_defined
    logger.debug(all7Types)

    types = get_all_prod_types(urllist, client)
    assert 'fdi.dataset.testproducts.DemoProduct' in types
    uniq = str(time.time())
    resPrds = []
    resPrd, resMap = [], []
    for i, full_cls in enumerate(csdb_7types_defined):
        assert full_cls in types
        cls = full_cls.rsplit('.', 1)[1]
        if i:
            ptype = Classes.mapping[cls]
            r = pstore.save(ptype(f'demo {cls} {uniq}'))
        else:
            # the first is DemoProduct
            assert cls == 'DemoProduct'
            r = pstore.save(get_demo_product(f'csdb test Demo_Product {uniq}'))
        if cls == 'TP':
            resPrd.append(r)
        elif cls == 'TM':
            resMap.append(r)
        resPrds.append(r)
    assert not test_pool.isEmpty()
    #pinfo = test_pool.getPoolInfo()

    return test_pool, resPrd, resMap, uniq, resPrds, pstore


def test_csdb_upload(csdb_uploaded):
    logger.info('test upload multiple products')
    test_pool, resPrd, resMap, uniq, resPrds, pstore = csdb_uploaded

    # urn:{poolname}:fdi.dataset.testproducts.TP:x
    assert all(csdb_pool_id in x.urn for x in resPrd)
    assert all('TP' in x.urn for x in resPrd)
    assert all(csdb_pool_id in x.urn for x in resMap)
    assert all('TM' in x.urn for x in resMap)

    for ele in resPrds:
        assert csdb_pool_id in ele.urn
        assert uniq in ele.product.description


def test_csdb_loadPrd(csdb_uploaded):
    logger.info('test load product')
    # test_pool, url, pstore = csdb

    test_pool, resPrd, resMap, uniq, resPrds, pstore = csdb_uploaded
    pinfo = test_pool.getPoolInfo()
    # for cl in pinfo[test_pool.poolname]['_classes']:
    #    if c['productTypeName'] == 'fdi.dataset.product.Product':
    #        rdIndex = c['currentSN']
    #        break
    urns = list(r.urn for r in resPrds)
    us = list(pinfo[test_pool.poolname]['_urns'].keys())
    for u in urns:
        prd = pstore.load(u).product
        assert prd.description.endswith(uniq), 'retrieve production incorrect'


@ pytest.fixture(scope='function')
def test_csdb_addTag(csdb_uploaded):
    logger.info('test add tag to urn')
    # test_pool, url, pstore = csdb

    test_pool, resPrd, resMap, uniq, resPrds, pstore = csdb_uploaded
    pinfo = test_pool.getPoolInfo()
    tag = 'test_prd'
    typename = list(pinfo[test_pool.poolname]['_classes'])[0]
    rdIndex = pinfo[test_pool.poolname]['_classes'][typename]['sn'][0]
    urn = 'urn:' + csdb_pool_id + ':' + typename + ':' + str(rdIndex)
    test_pool.setTag(tag, urn)
    assert tag in test_pool.getTags(urn)
    tag1 = 'test_prd1'
    tag2 = ['test_prd2', 'test_prd3']
    typename2 = list(pinfo[test_pool.poolname]['_classes'])[1]
    rdIndex2 = pinfo[test_pool.poolname]['_classes'][typename2]['sn'][0]
    urn2 = 'urn:' + csdb_pool_id + ':' + typename2 + ':' + str(rdIndex2)
    test_pool.setTag(tag1, urn2)
    test_pool.setTag(tag2, urn2)
    tagsall = [tag1]+tag2
    assert set(test_pool.getTags(urn2)) == set(tagsall)
    return test_pool, tag, urn, tagsall, urn2


def test_csdb_delTag(test_csdb_addTag):
    logger.info('test delete a tag')

    test_pool, tag, urn, tag2, urn2 = test_csdb_addTag
    assert tag in test_pool.getTags(urn)
    test_pool.removeTag(tag)
    test_pool.getPoolInfo()
    assert tag not in test_pool.getTags(urn)
    assert tag2[0] in test_pool.getTags(urn2)
    assert tag2[1] in test_pool.getTags(urn2)
    test_pool.removeTag(tag2[1])
    test_pool.getPoolInfo()
    assert tag2[1] not in test_pool.getTags(urn2)
    assert tag2[0] in test_pool.getTags(urn2)


def test_csdb_count(csdb_uploaded):
    logger.info('test count')
    # test_pool, url, pstore = csdb

    # start with none-empty
    test_pool, resPrd, resMap, uniq, resPrds, pstore = csdb_uploaded
    poolname = test_pool.poolname

    pinfo = test_pool.getPoolInfo()
    typename = resPrd[0].urnobj.getTypeName()

    count = test_pool.getCount(typename)
    np = len(resPrd)
    assert count == len(pinfo[poolname]['_classes'][typename]['sn'])
    assert count >= np

    # wipe pool
    pstore.wipePool()
    assert test_pool.isEmpty()
    pinfo = test_pool.getPoolInfo()
    count = test_pool.getCount(typename)
    assert count == 0

    # add prods again.
    prds = genProduct(
        3, unique=uniq, prod_cls=Classes.mapping[typename.rsplit('.', 1)[-1]])
    resPrds2 = pstore.save(prds)
    # pinfo = test_pool.getPoolInfo()
    assert len(resPrds2) == 3

    pinfo = test_pool.getPoolInfo()
    count = test_pool.getCount(typename)
    clz = pinfo[poolname]['_classes']
    assert typename in clz
    assert count == len(clz[typename]['sn']) == 3


def test_csdb_remove(csdb_uploaded):
    logger.info('test remove product')
    # test_pool, url, pstore = csdb
    test_pool, resPrd, resMap, uniq, resPrds, pstore = csdb_uploaded
    poolname = test_pool.poolname
    pinfo = test_pool.getPoolInfo()
    typename = resPrd[0].urnobj.getTypeName()
    rdIndex = pinfo[poolname]['_classes'][typename]['sn'][-1]
    urn = 'urn:' + csdb_pool_id + ':' + typename + ':' + str(rdIndex)
    res = test_pool.remove(urn)
    assert res in ['success', 'Not found resource.'], res
    pinfo = test_pool.getPoolInfo()
    assert rdIndex not in pinfo[poolname]['_classes'][typename]['sn']


def test_csdb_wipe(csdb_uploaded):
    logger.info('test wipe all')
    # test_pool, url, pstore = csdb

    test_pool, resPrd, resMap, uniq, resPrds, pstore = csdb_uploaded
    poolname = test_pool.poolname
    pinfo = test_pool.getPoolInfo()
    typename = resPrd[0].urnobj.getTypeName()

    assert not test_pool.isEmpty()
    test_pool.schematicWipe()
    info = test_pool.getPoolInfo()
    # print(info)
    assert test_pool.isEmpty()
