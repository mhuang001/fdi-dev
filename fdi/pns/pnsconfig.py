# -*- coding: utf-8 -*-
from os.path import join
import logging
import getpass
import os

# logging level for server or possibly by client
pnsconfig = dict(logginglevel=logging.DEBUG)

# pool URL look up table
poolurl_of = {
    'e2e': 'http://10.0.10.114:9885/v0.6/e2e'
}
pnsconfig['lookup'] = poolurl_of

# components of the default poolurl

# the key must be uppercased
FLASK_CONF = pnsconfig

# Te be edited automatically with sed -i 's/^EXTHOST =.*$/EXTHOST = xxx/g' file
EXTHOST = '172.17.0.1'
EXTPORT = 9876

# base url for webserver. Update version if needed.
pnsconfig['api_version'] = 'v0.6'
pnsconfig['baseurl'] = '/' + pnsconfig['api_version']


# base url for pool, you must have permission of this path, for example : /home/user/Documents
# this base pool path will be added at the beginning of your pool urn when you init a pool like:
# pstore = PoolManager.getPool('/demopool_user'), it will create a pool at pc['base_poolpath']/demopool_user/
# User can disable  basepoolpath by: pstore = PoolManager.getPool('/demopool_user', use_default_poolpath=False). Also note that pool URL takes priority if given to getPool().
pnsconfig['base_poolpath'] = '/tmp'
pnsconfig['server_poolpath'] = '/var/www/httppool_server/data'  # For server
pnsconfig['defaultpool'] = 'pool_default'

conf = 'server_test'
if conf == 'dev':
    # username, passwd, flask ip, flask port
    pnsconfig['node'] = {'username': 'foo',
                         'password': 'bar', 'host': '0.0.0.0', 'port': 5000}

    # server permission user
    pnsconfig['serveruser'] = 'mh'
    # PTS app permission user
    pnsconfig['ptsuser'] = 'mh'
    # on server
    home = '/cygdrive/c/Users/mh'
    pnsconfig['base_poolpath'] = '/tmp'
    pnsconfig['server_poolpath'] = '/tmp/data'  # For server
    pnsconfig['defaultpool'] = 'pool_default'
elif conf == 'server_test':
    pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                         'host': '127.0.0.1', 'port': 9884}

    # server permission user
    pnsconfig['serveruser'] = 'apache'
    # PTS app permission user
    pnsconfig['ptsuser'] = 'pns'
    # on server
    home = '/home'
elif conf == 'external':
    # wsgi behind apach2. cannot use env vars
    pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                         'host': EXTHOST, 'port': EXTPORT}

    # server permission user
    pnsconfig['serveruser'] = 'apache'
    # PTS app permission user
    pnsconfig['ptsuser'] = 'pns'
    # on server
    home = '/home'

pnsconfig['auth_user'] = pnsconfig['node']['username']
pnsconfig['auth_pass'] = pnsconfig['node']['password']
pnsconfig['httphost'] = 'http://' + \
    pnsconfig['node']['host']+':'+str(pnsconfig['node']['port'])
pnsconfig['poolprefix'] = pnsconfig['httphost']
pnsconfig['mysql'] = {'host': 'ssa-mysql', 'port': 3306,
                      'user': 'root',  'password': '123456',
                      'database': 'users'}


# import user classes
# See document in :class:`Classes`
pnsconfig['userclasses'] = ''


########### PNS-specific setup ############

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
