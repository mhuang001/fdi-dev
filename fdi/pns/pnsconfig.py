# -*- coding: utf-8 -*-
from os.path import join
import logging
import getpass
import pwd

# logging level for server or possibly by client
pnsconfig = dict(logginglevel=logging.DEBUG)

# base url for webserver. Update version if needed.
pnsconfig['api_version'] = 'v0.6'
pnsconfig['baseurl'] = '/' + pnsconfig['api_version']

# base url for pool, you must have permission of this path, for example : /home/user/Documents
# this base pool path will be added at the beginning of your pool urn when you init a pool like:
# pstore = PoolManager.getPool('/demopool_user'), it will create a pool at /data.demopool_user/
# User can disable  basepoolpath by: pstore = PoolManager.getPool('/demopool_user', use_default_poolpath=False)
pnsconfig['base_poolpath'] = '/tmp'
pnsconfig['server_poolpath'] = '/tmp/data'  # For server
pnsconfig['defaultpool'] = 'pool_default'

dev = 1
if dev:
    # username, passwd, flask ip, flask port
    pnsconfig['node'] = {'username': 'foo',
                         'password': 'bar', 'host': '0.0.0.0', 'port': 5000}

    # server permission user
    pnsconfig['serveruser'] = 'mh'
    # PTS app permission user
    pnsconfig['ptsuser'] = 'mh'
    # on server
    home = '/cygdrive/c/Users/mh'
else:
    pnsconfig['node'] = {'username': 'luchangfa', 'password': '123456',
                         'host': '10.0.10.114', 'port': 9888}

    # server permission user
    pnsconfig['serveruser'] = 'apache'
    # PTS app permission user
    pnsconfig['ptsuser'] = 'pns'
    # on server
    home = '/root'

pnsconfig['auth_user'] = pnsconfig['node']['username']
pnsconfig['auth_pass'] = pnsconfig['node']['password']
pnsconfig['httphost'] = 'http://' + \
    pnsconfig['node']['host']+':'+str(pnsconfig['node']['port'])
pnsconfig['poolprefix'] = pnsconfig['httphost']
pnsconfig['mysql'] = {'host': 'ssa-mysql', 'port': 3306,
                      'user': 'root',  'password': '123456',
                      'database': 'users'}

# import user classes
# '/cygdrive/d/code/share/svom/products/projectclasses.py'
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
