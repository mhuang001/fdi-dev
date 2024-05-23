
import threading
from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize
from ..dataset.classes import Class_Look_Up
from ..utils.getconfig import getConfig
from ..utils.common import trbk, lls
from ..pal import webapi
from ..pal.poolmanager import dbg_7types
from .fdi_requests import reqst, cached_json_dumps
from ..httppool.session import requests_retry_session
from ..pns.jsonio import auth_headers

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
poolpath = '/csdb/v1'

AUTHUSER = pcc['cloud_user']
AUTHPASS = pcc['cloud_pass']


@functools.lru_cache(maxsize=16)
def getAuth(user=AUTHUSER, password=AUTHPASS):
    return HTTPBasicAuth(user, password)


lock_r = threading.Lock()
lock_w = threading.Lock()


def read_from_cloud(requestName, client=None, asyn=False, server_type='csdb', user_urlbase=None, **kwds):
    """Apply GET method to CSDB server and get reply info back.

    if k-v parameters in kwds are simple values, return simple result,
    or parts of them; is v is a list, return a list of values of each
    member of v.

    Parameters
    ----------
    requestName : str
    client : str, method-func
    user_urlbase: str If given non_None value, will be used to prepend API-logic fragment to get URL.
    asyn : bool
        Run asynchronously. On of the parameters must be a list.
    user_urlbase : str
        The part of poolurl that is ommited in API document as constant base.
    **kwds :

    Returns
    -------
    obj, list

    Raises
    ------
    ValueError


    """
    
    # for token related, the base url is http://ip:port. everything
    # else http://ip:port/csdb/v1
    uub = f"{user_urlbase}{poolpath}" if user_urlbase else default_base
    # http://ip:port
    uub1 = user_urlbase if user_urlbase else defaulturl
    if client is None:
        client = session
    header = auth_headers()
    header['Content-Type'] = 'application/json;charset=UTF-8'
    if requestName == 'getToken':
        header['X-AUTH-TOKEN'] = kwds.pop('token', '')
        with lock_r:
            requestAPI =  uub1 + '/user/auth/token'
            if client is None or not getattr(client, 'auth', ''):
                postData = {
                    #'aesFlag':  False,
                    'username': AUTHUSER,
                    'password': AUTHPASS}
            else:
                postData = {
                    #'aesFlag': False,
                    'username': client.auth.username,
                    'password': client.auth.password}

            res = reqst(client.post, requestAPI, headers=header,
                        data=serialize(postData), server_type=server_type, auth=client.auth, **kwds)
    elif requestName == 'verifyToken':
    
        # e.g. http://10.0.0.2:8888
        with lock_r:
            _t = kwds.pop('token', '')
            if not _t:
                _t = ''
            requestAPI = uub1 + \
                '/user/auth/verify?token=' + _t
           # None is sucessful!
            res = reqst(client.get, requestAPI,
                        server_type=server_type, auth=client.auth, **kwds)
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
                        server_type=server_type, auth=client.auth, **kwds)
    elif requestName[0:4] == 'info':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            if requestName == 'infoUrn':
                requestAPI = uub + \
                    '/storage/info?urns=' + kwds.pop('urn')
            elif requestName == 'infoPool':
                limit = kwds.pop('limit', 10000)
                getc = 1 if kwds.pop('getCount', 0) else 0
                requestAPI = uub + \
                    f'/storage/info?getCount={getc}&pageIndex=1&pageSize={limit}&pools=' + \
                    kwds.pop('pools')
            else:
                raise ValueError("Unknown request API: " + str(requestName))
            res = reqst(client.get, requestAPI, headers=header,
                        server_type=server_type, auth=client.auth, **kwds)

    elif requestName == 'getMeta':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = uub + \
                '/storage/meta?urn=' + kwds.pop('urn')
            res = reqst(client.get, requestAPI, headers=header,
                        server_type=server_type, auth=client.auth, **kwds)
            return res['_ATTR_meta']
    elif requestName == 'getDataInfo':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI0 = uub + \
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
                              server_type=server_type,
                              auth=client.auth, cookies=client.cookies,
                              **kwds)
                re = dict(zip(pp_one_pool, reses))
            else:
                re = {}
                for p in pp_one_pool:
                    requestAPI = requestAPI1 + p
                    r = reqst(client.get, requestAPI, headers=header,
                              server_type=server_type, auth=client.auth, **kwds)

                    re[p] = r
            # reconstruct
            res = [re[x] for x in pp]
            return res if listpa else res[0]

    elif requestName == 'getDataType':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            subs = kwds.pop('substring', '')
            requestAPI = uub + \
                '/datatype/list' + (f'?substring={subs}' if subs else '')
            res = reqst(client.get, requestAPI, headers=header,
                        server_type=server_type, auth=client.auth, **kwds)

    elif requestName == 'uploadDataType':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            header["accept"] = "*/*"
            # somehow application/json will cause error "unsupported"
            # = 'application/json'  # ;charset=UTF-8'
            # must delete so it will be changed to multipart
            del header['Content-Type']
            del header['Content-type']
            requestAPI = uub + \
                '/datatype/upload'
            ea=kwds.pop('ensure_ascii', True),
            cls_full_name = kwds.pop('cls_full_name')
            pkd = kwds.pop('picked', None)
            ind=kwds.pop('indent', 2)
            if pkd:
                jsn = pkd
            else:
                jsn = cached_json_dumps(cls_full_name,
                                        ensure_ascii=ea,
                                        indent=ind,
                                        des=True
                                        )
            fdata = {"file": (cls_full_name, jsn)}
            data = {"metaPath": kwds.pop('metaPath',
                                         "/product_keywords"),
                    "productType": cls_full_name}

            res = reqst(client.post, requestAPI,
                        files=fdata, data=data, headers=header, server_type=server_type, auth=client.auth, **kwds)
    elif requestName == 'defineProductTypes':
        # based on example http://123.56.102.90:31101/sources/satellite-data-pipeline/-/blob/master/csdb/csdb/csdb.py#L232
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            header["accept"] = "*/*"
            # somehow application/json will cause error "unsupported"
            # = 'application/json'  # ;charset=UTF-8'
            # fileContentType=application/fits according to the example.
            fileContentType = 'application/fits'
            del header['Content-Type'] # = fileContentType
            requestAPI = uub + \
                '/datatype/uploadProductTypes'

            ea = kwds.pop('ensure_ascii', True),
            cls_full_name = kwds.pop('cls_full_name')
            pkd = kwds.pop('picked', None)
            ind = kwds.pop('indent', 2)
            if pkd:
                jsn = pkd
            else:
                jsn = cached_json_dumps(cls_full_name,
                                        ensure_ascii=ea,
                                        indent=ind,
                                        des=True
                                        )
            # fdata = {"file": (cls_full_name, jsn)}
            # example: response = requests.post(url=url, files=files, headers=headers)
            files = {"file": ("file", jsn, fileContentType)}

            res = reqst(client.post, requestAPI,
                        files=files, headers=header,
                        server_type=server_type, auth=client.auth, **kwds)

    elif requestName == 'delDataTypeData':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI0 = uub + \
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
                            server_type=server_type, auth=client.auth, **kwds)
            else:
                rs = []
                for a in apis:
                    r = reqst(client.delete, a, headers=header,
                              server_type=server_type, auth=client.auth, **kwds)
                    rs.append(r)
                res = rs if alist else rs[0]
    elif requestName == 'remove':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI0 = uub + \
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
                          server_type=server_type, auth=client.auth, **kwds)
                rs = [0 if x is None else 1 for x in r]
            else:
                rs = []
                for a in apis:
                    r = reqst(client.post, a, headers=header,
                              server_type=server_type, auth=client.auth, **kwds)
                    rs.append(0 if r is None else 1)
            res = rs if alist else rs[0]
    elif requestName == 'existPool':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = uub + \
                '/pool/info?storagePoolName=' + kwds.pop('poolname')
            res = reqst(client.get, requestAPI, headers=header,
                        server_type=server_type, auth=client.auth, **kwds)
    elif requestName == 'createPool':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = uub + \
                '/pool/create?poolName=' + \
                kwds.pop('poolname') + '&read=0&write=0'
            res = reqst(client.post, requestAPI, headers=header,
                        server_type=server_type, auth=client.auth, **kwds)
    elif requestName == 'listPool':
        with lock_r:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = uub + \
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
                        server_type=server_type, auth=client.auth, **kwds)
    elif requestName == 'wipePool':
        with lock_w:
            tk = kwds.pop('token', '')
            header['X-AUTH-TOKEN'] = tk
            keep_pool = 'resetSN=1&' if kwds.pop('keep', True) else ''
            requestAPI = uub + \
                f'/pool/delete?{keep_pool}storagePoolName=' + \
                kwds.pop('poolname')
            #######
            if dbg_7types:
                tl = read_from_cloud(
                    'getDataType', substring='testproducts', token=tk)
                print('<'*21, len(tl), tl)

            res = reqst(client.post, requestAPI, headers=header,
                        server_type=server_type, auth=client.auth, **kwds)
            #######
            if dbg_7types:
                tl = read_from_cloud(
                    'getDataType', substring='testproducts', token=tk)
                print('>'*21, len(tl), tl)
                print(requestAPI, res)
    elif requestName == 'restorePool':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI = uub + \
                '/pool/restore?storagePoolName=' + kwds.pop('poolname')
            res = reqst(client.post, requestAPI, headers=header,
                        server_type=server_type, auth=client.auth, **kwds)
    elif requestName == 'addTag':
        with lock_w:
            header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            requestAPI0 = uub + \
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
                            server_type=server_type, auth=client.auth, **kwds)
            else:
                rs = []
                for a in apis:
                    r = reqst(client.get, a, headers=header,
                              server_type=server_type, auth=client.auth, **kwds)
                    rs.append(r)
                res = rs if alist else rs[0]
    elif requestName in ('tagExist',
                         'getTag'):
        with lock_r:
            if requestName == 'getTag':
                requestAPI0 = uub + \
                    '/storage/tag?tag='
            else:
                requestAPI0 = uub + \
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
                          server_type=server_type, auth=client.auth, **kwds)
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


def load_from_cloud(requestName, client=None, asyn=False, server_type='csdb', user_urlbase=None, **kwds):

    if client is None:
        client = session
    # ends with +'/csdb/v1'
    uub = f"{user_urlbase}{poolpath}" if user_urlbase else default_base
    requestAPI = uub
    header = {'Content-Type': 'application/json;charset=UTF-8'}

    if requestName == 'uploadProduct':
        with lock_w:
            # application/json causes "only allow use multipart/form-data"
            del header['Content-Type']
            header['X-CSDB-AUTOINDEX'] = '1'
            # if not given use default
            mp = kwds.pop('metaPath','/_ATTR_meta')
            # if given none make no header
            if mp:
                header['X-CSDB-METADATA'] = mp
            else:
                header.pop('X-CSDB-METADATA', None)
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
            con = kwds.pop('content', None)
            #con = 'application/octet-stream'
            if asyn:
                # data = [{'file': (f, p), 'tags': t}
                #         for f, p, t in zip(fileNames, prds, tags)]
                data = []
                for f, p, t in zip(fileNames, prds, tags):
                    d = aiohttp.FormData()
                    d.add_field('file', p,
                                content_type=con, filename=f)
                    if t:
                        d.add_field('tags', t)
                    data.append(d)
            else:
                files = [{'file': ('file', p, con) if con else p,
                          #'tags': t, 'productType':_f
                          } for f, p, t in zip(fileNames, prds, tags)]
                data = [{"tags":t,
                         #"productType":f
                         } for t, f in zip(tags, fileNames)
                        ]
                headers = _multi_input_header(kwds, n, header)

            serialize_out = kwds.pop('serialize_out', '')
            if asyn:
                res = reqst('post', apis, data=data,
                            headers=headers, server_type=server_type, auth=client.auth, **kwds)
            else:
                res = []
                for a, f, d, h in zip(apis, files, data, headers):
                    r = reqst(client.post, a, files=f, data=d,
                              headers=h, server_type=server_type,
                              auth=client.auth, **kwds)
                    res.append(r)

            return res if alist else res[0]

    elif requestName == 'pullProduct':
        with lock_r:
            # header['X-AUTH-TOKEN'] = kwds.pop('token', '')
            # requestAPI = requestAPI + '/storage/get?urn=' + kwds.pop('urn', '')
            # res = reqst(client.get, requestAPI,
            #             headers=header, stream=True, server_type=server_type, auth=client.auth, **kwds)
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
                            server_type=server_type, auth=client.auth, **kwds)
            else:
                res = []
                for a, h in zip(apis, headers):
                    r = reqst(client.get, a, headers=h,
                              stream=True, server_type=server_type, auth=client.auth, **kwds)
                    res.append(r)
            return res if alist else res[0]
    else:
        raise ValueError(f'Unknown request API: {requestName}')


def delete_from_server(requestName, client=None, asyn=False, server_type='csdb', user_urlbase=None, **kwds):

    if client is None:
        client = session
    uub = f"{user_urlbase}{poolpath}" if user_urlbase else default_base
    requestAPI = uub
    
    header = {'Content-Type': 'application/json;charset=UTF-8'}
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
                            headers=header, server_type=server_type, auth=client.auth, **kwds)
            else:
                rs = []
                for a in apis:
                    r = reqst(client.delete, a, headers=header,
                              server_type=server_type, auth=client.auth, **kwds)
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

def cls2jsn(clsn, namespace):
    obj = namespace[clsn]()
    # return json.dumps(obj.zInfo, ensure_ascii=asci, indent=2)
    return obj.serialized(indent=2)

def add_a_dataType(full_name, jsn, client, urlup):
    """ not using client fixture. returns csdb ['data'] result. """
    hdr = {"accept": "*/*"}
    fdata = {"file": (full_name, jsn)}
    data = {"metaPath": "/metadata", "productType": full_name}
    x = reqst(client.post, apis=urlup, files=fdata,
              data=data, headers=hdr)
    return x


def get_all_product_types_on_server(urllist, client):
    x = client.get(urllist)

    if x.status_code != 200:
        raise RuntimeError( 'Unsuccessful response %d.' % aResponse.status_code)

    a = x.text
    o, code = deserialize(a, int_key=True),  x.status_code

    types = o['data'] if issubclass(o.__class__, dict) else a
    return types


def upload_defintion(full_cls, urlcsdb,
                     client=None, check=True, skip=False, namespace=None):
    """ Client level implementation to upload the definition of given class.
    Not using fixture. ref tests/serv/test_csdb.py `test_upload_All_prod_defn` as an example.
    
    Parameters
    ----------
    skip :    bool
         If set `full_cls` will be skipped if exists on the server.
    """
    urlupload = urlcsdb + '/datatype/upload'
    urldelete = urlcsdb + '/datatype/'
    urllist = urlcsdb + '/datatype/list'

    if namespace is None:
        namespace = Class_Look_Up
    
    if isinstance(full_cls, list):
        alist = True
        fs = full_cls
    else:
        alist = False
        fs = [full_cls]

    # upload
    for f in fs:
        if skip:
            # check type exists
            x = client.get(urllist + '?substring=' + f)
            o, code = getPayload(x)
            if f in o['data']:  # must not "in o['data']" as TC will fall throught due to TCC
                continue
        payload = cls2jsn(f.rsplit('.', 1)[-1], namespace)
        r = add_a_dataType(f, payload, client=client, urlup=urlupload)
        assert r.status_code == 200, r.reason
        logger.info(f'uploaded definition of {f}')
    if check:
        # check ptypes again
        ptypes = get_all_product_types_on_server(urllist, client)
        # print(ptypes)
        for f in fs:
            assert f in ptypes
        logger.info(f'Checked existence of all {len(fs)}')
    return fs if alist else fs[0]


