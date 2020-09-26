# -*- coding: utf-8 -*-
from os.path import join
import logging
import getpass
import pwd

# logging level for server or possibly by client
pnsconfig = dict(logginglevel=logging.INFO)

# base url for webserver. Update version if needed.
pnsconfig['baseurl'] = '/v0.6'
pnsconfig['auth_user'] = 'gsegment'
pnsconfig['auth_pass'] = '123456'
pnsconfig['httppoolurl'] = '/httppool'
pnsconfig['httphost'] = 'http://192.168.1.9:5000'

pnsconfig['auth_user'] = 'luchangfa'
pnsconfig['auth_pass'] = '123456'
pnsconfig['httppoolurl'] = '/httppool'
pnsconfig['httphost'] = 'http://10.0.10.114:9888'
# base url for pool, you must have permission of this path, for example : /home/user/Documents
# this base pool path will be added at the beginning of your pool urn when you init a pool like:
# pstore = PoolManager.getPool('/demopool_user'), it will create a pool at /data.demopool_user/
# User can disable  basepoolpath by: pstore = PoolManager.getPool('/demopool_user', use_default_poolpath=False)
pnsconfig['basepoolpath_client'] = '/tmp'
pnsconfig['basepoolpath'] = '/data/' # For server
pnsconfig['defaultpool'] = 'pool_default'
dev = 0
if dev:
    pnsconfig['poolprefix'] = 'http://192.168.1.9:5000'
    # username, passwd, flask ip, flask port
    pnsconfig['node'] = {'username': 'foo',
                         'password': 'bar', 'host': '0.0.0.0', 'port': 5000}

    # server permission user. default is current user
    pnsconfig['serveruser'] = getpass.getuser()
    # PTS app permission user. default is pnsconfig['serveruser']
    pnsconfig['ptsuser'] = pnsconfig['serveruser']
    # the directory where the pns ome is on server. default is ptsuser home
    home = pwd.getpwnam(pnsconfig['ptsuser']).pw_dir

    pnsconfig['mysql'] = {'host': 'localhost',  'port':3306, 'user': 'root',  'password': 'toto', 'database': 'users'}
else:
    pnsconfig['poolprefix'] = 'http://10.0.10.114:9888'
    pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                         'host': '10.0.10.114', 'port': 9888 }

    pnsconfig['mysql'] = {'host': 'ssa-mysql', 'port':3306, 'user': 'root',  'password': '123456', 'database': 'users'}

    # server permission user
    pnsconfig['serveruser'] = getpass.getuser()
    # PTS app permission user
    pnsconfig['ptsuser'] = getpass.getuser()
    # on server
    home = '/root'

# import user classes
pnsconfig['userclasses'] = ''

phome = join(home, 'pns')
pnsconfig['paths'] = dict(
    pnshome=phome,
    inputdir=join(phome, 'input'),
    inputfiles=['pns.cat', 'pns.pn'],
    outputdir=join(phome, 'output'),
    outputfiles=['xycc.dat', 'atc.cc']
)

# the stateless data processing program that reads from inputdir and
# leave the output in the outputdir. The format is the input for subprocess()
h = pnsconfig['paths']['pnshome']
pnsconfig['scripts'] = dict(
    init=[join(h, 'initPTS'), ''],
    config=[join(h, 'configPTS'), ''],
    run=[join(h, 'runPTS'), ''],
    clean=[join(h, 'cleanPTS'), '']
)
del phome, h

# seconds
pnsconfig['timeout'] = 10
