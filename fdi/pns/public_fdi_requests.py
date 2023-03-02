
import threading
from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize
from ..utils.getconfig import getConfig
from ..utils.common import trbk, lls
from ..pal import webapi
from .fdi_requests import reqst, cached_json_dumps
from ..httppool.session import requests_retry_session

import aiohttp
from urllib.parse import quote

import functools
import logging
import sys
import json
import copy

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
    from urllib.parse import urlparse
else:
    PY3 = False
    # strset = (str, unicode)
    strset = str
    from urlparse import urlparse

logger = logging.getLogger(__name__)
# logger.debug('level %d' % (logger.getEffectiveLevel()))

session = requests_retry_session()

pcc = getConfig()
defaulturl = 'http://' + pcc['cloud_host'] + \
             ':' + str(pcc['cloud_port'])
default_base = defaulturl + pcc['cloud_api_base'] + \
    '/' + pcc['cloud_api_version']
AUTHUSER = pcc['cloud_username']
AUTHPASS = pcc['cloud_password']


@functools.lru_cache(maxsize=16)
def getAuth(user=AUTHUSER, password=AUTHPASS):
    return HTTPBasicAuth(user, password)


lock_r = threading.Lock()
lock_w = threading.Lock()


def read_from_cloud(requestName, client=None, asyn=False, server_type='csdb', **kwds):
    """Apply GET method to CSDB server and get reply info back.

    if k-v parameters in kwds are simple values, return simple result,
    or parts of them; is v is a list, return a list of values of each
    member of v.

    Parameters
    ----------
    requestName : str
    client : str, method-func
    asyn : bool
        Run asynchronously. On of the parameters must be a list.
    **kwds :

    Returns
    -------
    obj, list

    Raises
    ------
    ValueError


    """

    if client is None:
        client = session
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    if requestName == 'getToken':
        header['X-AUTH-TOKEN'] = kwds.pop('token', '')
        with lock_r:
            requestAPI = defaulturl + '/user/auth/token'
            postData = {'username': AUTHUSER, 'password': AUTHPASS}
            res = reqst(client.post, requestAPI, headers=header,
                        data=serialize(postData), server_type=server_type, **kwds)
    elif requestName == 'verifyToken':
        with lock_r:
            requestAPI = defaulturl + \
                '/user/auth/verify?token=' + kwds.pop('token', '')
            res = reqst(client.get, requestAPI,
                        server_type=server_type, **kwds)
    elif requestName == 'poolLogInfo':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = default_base + \
                '/pool/poolLogInfo'
            data = kwds.pop('data', """{
                "endTime": "",
                "fileName": "",
                "page": 1,
                "pageSize": 2,
                "startTime": "",
                "status": "",
                "userName": ""
            }""")
            res = reqst(client.post, requestAPI, headers=header,
                        data=data,
                        server_type=server_type, **kwds)
    elif requestName[0:4] == 'info':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            if requestName == 'infoUrn':
                requestAPI = default_base + \
                    '/storage/info?urns=' + kwds.pop('urn')
            elif requestName == 'infoPool':
                limit = kwds.pop('limit', 10000)
                getc = 1 if kwds.pop('getCount', 0) else 0
                requestAPI = default_base + \
                    f'/storage/info?getCount={getc}&pageIndex=1&pageSize={limit}&pools=' + \
                    kwds.pop('pools')
            else:
                raise ValueError("Unknown request API: " + str(requestName))
            res = reqst(client.get, requestAPI, headers=header,
                        server_type=server_type, **kwds)

    elif requestName == 'getMeta':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = default_base + \
                '/storage/meta?urn=' + kwds.pop('urn')
            res = reqst(client.get, requestAPI, headers=header,
                        server_type=server_type, **kwds)
            return res['_ATTR_meta']
    elif requestName == 'getDataInfo':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI0 = default_base + \
                '/storage/searchByPoolOrPath?limitCount=%d'

            """ result example:
            {
                  "code": 0,
                  "msg": "OK",
                  "data": [
                    {
                      "url": "http://...:.../csdb/v1/storage/test_csdb_fdi/fdi.dataset.testproducts.TCC/732",
                      "path": "/test_csdb_fdi/fdi.dataset.testproducts.TCC/732",
                      "urn": "urn:test_csdb_fdi:fdi.dataset.testproducts.TCC:732",
                      "timestamp": 1675267011883,
                      "tags": [],
                      "index": 732,
                      "md5": "2FCC79CA9F0FD0A671D45FAC35528465",
                      "size": 5246,
                      "contentType": null,
                      "fileName": "fdi.dataset.testproducts.TCC",
                      "dataType": "fdi.dataset.testproducts.TCC"
                    },
                    ...
                          ],
                    "total": 84
             }
            """
            # paths can be URNs
            paths = kwds.pop('paths', '')
            pool = kwds.pop('pool', None)

            listpa = isinstance(paths, (list, tuple))
            if not listpa:
                paths = [paths]
            po = f'&pool={pool}' if pool else ''
            # this remembers all members
            pp = []
            # this has only one that has pool
            pp_one_pool = []
            for a in paths:
                if a:
                    if a.startswith('urn:'):
                        a = a[3:].replace(':', '/')
                    seg = f'&path={a}'
                    pp.append(seg)
                    pp_one_pool.append(seg)
                else:
                    pp.append(po)
                    if not pp_one_pool:
                        pp_one_pool.append(po)
            limit = kwds.pop('limit', 10000)
            # max length with one extra
            requestAPI1 = requestAPI0 % (limit)
            if asyn:
                apis = [requestAPI1+p for p in pp_one_pool]
                reses = reqst('get', apis, headers=header,
                              server_type=server_type, **kwds)
                re = dict(zip(pp_one_pool, reses))
            else:
                re = {}
                for p in pp_one_pool:
                    requestAPI = requestAPI1 + p
                    r = reqst(client.get, requestAPI, headers=header,
                              server_type=server_type, **kwds)

                    re[p] = r
            # reconstruct
            res = [re[x] for x in pp]
            return res if listpa else res[0]

    elif requestName == 'getDataType':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')

            requestAPI = default_base + \
                '/datatype/list'
            res = reqst(client.get, requestAPI, headers=header,
                        server_type=server_type, **kwds)

    elif requestName == 'uploadDataType':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            header["accept"] = "*/*"
            # somehow application/json will cause error "unsupported"
            # = 'application/json'  # ;charset=UTF-8'
            del header['Content-Type']
            requestAPI = default_base + \
                '/datatype/upload'
            cls_full_name = kwds.pop('cls_full_name')
            jsn = cached_json_dumps(cls_full_name,
                                    ensure_ascii=kwds.get(
                                        'ensure_ascii', True),
                                    indent=kwds.get('indent', 2))
            fdata = {"file": (cls_full_name, jsn)}
            data = {"metaPath": "/metadata",
                    "dataType": cls_full_name}
            res = reqst(client.post, requestAPI,
                        files=fdata, data=data, headers=header, server_type=server_type, **kwds)
    elif requestName == 'delDataTypeData':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI0 = default_base + \
                f'/storage/delDatatypeData?path='
            _p = kwds.pop('path')
            if isinstance(_p, str):
                paths = [_p]
                alist = False
            else:
                paths = _p
                alist = True
            apis = [requestAPI0+p for p in paths]
            if asyn:
                res = reqst('delete', apis, headers=header,
                            server_type=server_type, **kwds)
            else:
                rs = []
                for a in apis:
                    r = reqst(client.delete, a, headers=header,
                              server_type=server_type, **kwds)
                    rs.append(r)
                res = rs if alist else rs[0]
    elif requestName == 'remove':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI0 = default_base + \
                '/storage/deleteData?path='
            _p = kwds.pop('path', '')
            if isinstance(_p, str):
                paths = [_p]
                alist = False
            else:
                paths = _p
                alist = True

            apis = [requestAPI0+p for p in paths]
            if asyn:
                r = reqst('post', apis, headers=header,
                          server_type=server_type, **kwds)
                rs = [0 if x is None else 1 for x in r]
            else:
                rs = []
                for a in apis:
                    r = reqst(client.post, a, headers=header,
                              server_type=server_type, **kwds)
                    rs.append(0 if r is None else 1)
            res = rs if alist else rs[0]
    elif requestName == 'existPool':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = default_base + \
                '/pool/info?storagePoolName=' + kwds.pop('poolname')
            res = reqst(client.get, requestAPI, headers=header,
                        server_type=server_type, **kwds)
    elif requestName == 'createPool':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = default_base + \
                '/pool/create?poolName=' + \
                kwds.pop('poolname') + '&read=0&write=0'
            res = reqst(client.post, requestAPI, headers=header,
                        server_type=server_type, **kwds)
    elif requestName == 'listPool':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = default_base + \
                '/pool/list'
            data = kwds.pop('data', """{
                "endTime": "",
                "page": 1,
                "pageSize": 20,
                "poolName": "",
                "startTime": "",
                "status": ""
            }""")
            res = reqst(client.post, requestAPI, headers=header,
                        data=data,
                        server_type=server_type, **kwds)
    elif requestName == 'wipePool':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = default_base + \
                '/pool/delete?storagePoolName=' + kwds.pop('poolname')
            res = None if 0 else reqst(client.post, requestAPI, headers=header,
                                       server_type=server_type, **kwds)
    elif requestName == 'restorePool':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = default_base + \
                '/pool/restore?storagePoolName=' + kwds.pop('poolname')
            res = reqst(client.post, requestAPI, headers=header,
                        server_type=server_type, **kwds)
    elif requestName == 'addTag':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI0 = default_base + \
                '/storage/addTags?tags='

            _t = kwds.pop('tag')
            if isinstance(_t, str):
                tags = [_t]
                alist = False
            else:
                tags = _t
                alist = True
            u = '&urn=' + kwds.pop('urn')
            apis = [requestAPI0 + quote(t) + u for t in tags]
            if asyn:
                res = reqst('get', apis, headers=header,
                            server_type=server_type, **kwds)
            else:
                rs = []
                for a in apis:
                    r = reqst(client.get, a, headers=header,
                              server_type=server_type, **kwds)
                    rs.append(r)
                res = rs if alist else rs[0]
    elif requestName in ('tagExist',
                         'getUrn'):
        with lock_r:
            if requestName == 'getUrn':
                requestAPI0 = default_base + \
                    '/storage/tag?tag='
            else:
                requestAPI0 = default_base + \
                    '/storage/tagExist?tag='

            header['X-AUTH-TOKEN'] = kwds.pop('token', '')

            _t = kwds.pop('tag', None)
            if isinstance(_t, str) or _t is None:
                tags = [_t]
                alist = False
            else:
                tags = _t
                alist = True

            apis = [requestAPI0 + quote(t) for t in tags]
            rs = []
            for a in apis:
                r = reqst(client.get, a, headers=header,
                          server_type=server_type, **kwds)
                rs.append(r)
            res = rs if alist else rs[0]
    else:
        raise ValueError("Unknown request API: " + str(requestName))
    # print("Read from API: " + requestAPI)
    # must remove csdb layer
    return res


def _multi_input_header(kwds, n, header):

    _k = kwds.pop('token', '')
    withtokens = []
    for tok in (_k if isinstance(_k, list) else ([_k] * n)):
        w = copy.copy(header)
        w['X-AUTH-TOKEN'] = tok
        withtokens.append(w)

    _h = kwds.pop('header', {})
    if not isinstance(_h, list):
        for _ in withtokens:
            _.update(_h)
        headers = withtokens
    else:
        for hdr, tok in zip(_h, withtokens):
            hdr.update(tok)
        headers = _h
    return headers


def load_from_cloud(requestName, client=None, asyn=False, server_type='csdb', **kwds):
    if client is None:
        client = session
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    requestAPI = default_base

    if requestName == 'uploadProduct':
        with lock_w:
            # application/json causes "only allow use multipart/form-data"
            del header['Content-Type']
            header['X-CSDB-AUTOINDEX'] = '1'
            header['X-CSDB-METADATA'] = '/_ATTR_meta'
            header['X-CSDB-HASHCOMPARE'] = '0'

            requestAPI0 = requestAPI + \
                '/storage/upload'
            _p = kwds.pop('path', '')
            if isinstance(_p, str):
                paths = [_p]
                alist = False
            else:
                paths = _p
                alist = True
            apis = [
                (f'{requestAPI0}?path={p}' if p else requestAPI0) for p in paths]
            # all parameters, if is given a single value, will be expanded to a list of this size.
            n = len(apis)

            _pr = kwds.pop('products', None)
            if not isinstance(_pr, list):
                # XXX TODO: a better way to determine seriaized product
                prds = [_pr] * n
            else:
                prds = _pr

            _f = kwds.pop('resourcetype')
            if isinstance(_f, str):
                fileNames = [_f] * n
            else:
                fileNames = _f

            _t = kwds.pop('tags', None)
            if isinstance(_t, list):
                _t = ','.join(x for x in _t if x and x.strip())
            tags = [_t] * n

            if asyn:
                # data = [{'file': (f, p), 'tags': t}
                #         for f, p, t in zip(fileNames, prds, tags)]
                data = []
                for f, p, t in zip(fileNames, prds, tags):
                    d = aiohttp.FormData()
                    d.add_field('file', p,
                                content_type='application/json', filename=f)
                    if t:
                        d.add_field('tags', t)
                    data.append(d)
            else:
                files = [{'file': (f, p)} for f, p in zip(fileNames, prds)]
                data = [{'tags': t} for t in tags]

            headers = _multi_input_header(kwds, n, header)

            serialize_out = kwds.pop('serialize_out', '')
            if asyn:
                res = reqst('post', apis, data=data,
                            headers=headers, server_type=server_type, **kwds)
            else:
                res = []
                for a, f, d, h in zip(apis, files, data, headers):
                    r = reqst(client.post, a, files=f, data=d,
                              headers=h, server_type=server_type, **kwds)
                    res.append(r)
            return res if alist else res[0]

    elif requestName == 'pullProduct':
        with lock_r:
            # header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            # requestAPI = requestAPI + '/storage/get?urn=' + kwds.pop('urn', '')
            # res = reqst(client.get, requestAPI,
            #             headers=header, stream=True, server_type=server_type, **kwds)
            # TODO: save product to local

            requestAPI0 = requestAPI + '/storage/get?urn='
            _u = kwds.pop('urn', '')
            if isinstance(_u, list):
                alist = True
            else:
                urns = [_u]
                alist = False

            n = len(urns)

            headers = _multi_input_header(kwds, n, header)
            apis = [requestAPI0 + u for u in urns]

            if asyn:
                res = reqst('get', apis, headers=headers,
                            server_type=server_type, **kwds)
            else:
                res = []
                for a, h in zip(apis, headers):
                    r = reqst(client.get, a, headers=h,
                              stream=True, server_type=server_type, **kwds)
                    res.append(r)
            return res if alist else res[0]
    else:
        raise ValueError(f'Unknown request API: {requestName}')


def delete_from_server(requestName, client=None, asyn=False, server_type='csdb', **kwds):
    if client is None:
        client = session
    header = {'Content-Type': 'application/json;charset=UTF-8'}
    requestAPI = default_base
    if requestName == 'delTag':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI0 = requestAPI + '/storage/delTag?tag='

            _t = kwds.pop('tag', None)
            if isinstance(_t, str) or _t is None:
                tags = [_t]
                alist = False
            else:
                tags = _t
                alist = True
            apis = [requestAPI0 + quote(t) for t in tags]
            if asyn:
                res = reqst('delete', apis,
                            headers=header, server_type=server_type, **kwds)
            else:
                rs = []
                for a in apis:
                    r = reqst(client.delete, a, headers=header,
                              server_type=server_type, **kwds)
                    rs.append(r)
                res = rs if alist else rs[0]
    # print("Read from API: " + requestAPI)
    return res


def get_service_method(method):
    service = method.split('_')[0]
    serviceName = method.split('_')[1]
    if service not in webapi.PublicServices:
        return 'home', None
    return service, serviceName
