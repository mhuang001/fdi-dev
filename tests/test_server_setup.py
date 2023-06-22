

import pytest, os, sys, time

from fdi.testsupport.fixtures import BG_SERVER_LOG


def test_pool_server_url(server, pytestconfig):
    if os.path.exists(BG_SERVER_LOG):
        os.unlink(BG_SERVER_LOG)

    assert not os.path.exists(BG_SERVER_LOG)
    url, hdr = server
    assert url.startswith('http://127.0.0.1:9885/fdi/v')
    assert hdr['server_type'] in ['mock', 'live']
    assert pytestconfig.getoption('--server') in ['mock', 'background', 'external']
    print(url, hdr)
    #time.sleep(1000)

def test_pool_client_url(client, server):
    url, ty = server
    res = client.get(url).text
    assert 'docker  pool server' in res
    print(client.get(url).text)

def test_csdb_server_url(csdb_server):
    url, ty = csdb_server
    print(csdb_server)

def test_csdb_client_url(client, csdb_server):
    url, ty = csdb_server
    #print(csdb_client)
    res = client.get(url).text
    assert res.endswith('{"code":1,"msg":"Not authorization","total":0}')
    print(res)

    
#def para_server(pc, pytestconfig, new_user_read_write, request):
#    pytestconfig['--server'] = request.param
#    yield server #(pc, pytestconfig, new_user_read_write)
   
#@pytest.mark.server_arch('http')

#@pytest.mark.parametrize("server",[ 'mock','background'], indirect=True)

