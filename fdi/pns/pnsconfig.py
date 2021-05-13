# -*- coding: utf-8 -*-
from os.path import join
import logging
import getpass
import os

pnsconfig = {}

# look-up table for PoolManager (therefor HttpClient) to get pool URLs eith Pool ID (poolname)
poolurl_of = {
    'svom': 'http://10.0.10.114:9885/v0.6/svom'
}
pnsconfig['lookup'] = poolurl_of

###########################################
# Configuration for Servers running locally.
# components of the default poolurl

# the key (variable names) must be uppercased for Flask server
# FLASK_CONF = pnsconfig

# Te be edited automatically with sed -i 's/^EXTHOST =.*$/EXTHOST = xxx/g' file
EXTHOST = '172.17.0.1'
EXTPORT = 9876

# base url for webserver. Update version if needed.
pnsconfig['api_version'] = 'v0.8'
pnsconfig['baseurl'] = '/' + pnsconfig['api_version']


# default path of working directories for LocalPools.
pnsconfig['base_poolpath'] = '/tmp'
# default path of working directories for HttpPool server.
pnsconfig['server_poolpath'] = '/var/www/httppool_server/data'  # For server
# you must have write permission of above paths.
# For example : /home/user/Documents
# will be added at the beginning of request pool ID 'my_pool'
# when you init a server pool like:
# ``pstore = PoolManager.getPool('my_pool') without poolurl,
# the poolurl will become 'file:///home/user/Documents/my_pool'.
# creating a pool at pc['base_poolpath']
# See document of :meth:'PoolManager.getPool'

# logging level for server
pnsconfig['logginglevel'] = logging.DEBUG
# for HttpPool
pnsconfig['defaultpool'] = 'pool_default'

# choose from pre-defined.
conf = ['dev', 'server_test', 'external'][0]

# modify
if conf == 'dev':
    # username, passwd, flask ip, flask port
    pnsconfig['node'] = {'username': 'foo',
                         'password': 'bar', 'host': '0.0.0.0', 'port': 5000}

    # server permission user
    pnsconfig['serveruser'] = 'mh'
    pnsconfig['base_poolpath'] = '/tmp'
    pnsconfig['server_poolpath'] = '/tmp/data'  # For server
    # on pns server
    home = '/cygdrive/c/Users/mh'
    # PTS app permission user
    pnsconfig['ptsuser'] = 'mh'

elif conf == 'server_test':
    pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                         'host': '172.0.17.9', 'port': 9884}
    # server permission user
    pnsconfig['serveruser'] = 'apache'
    # PTS app permission user
    pnsconfig['ptsuser'] = 'pns'
    # on pns server
    home = '/home'
elif conf == 'external':
    # wsgi behind apach2. cannot use env vars
    pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                         'host': EXTHOST, 'port': EXTPORT}

    # server permission user
    pnsconfig['serveruser'] = 'apache'
    # PTS app permission user
    pnsconfig['ptsuser'] = 'pns'
    # on pns server
    home = '/home'
else:
    pass
pnsconfig['auth_user'] = pnsconfig['node']['username']
pnsconfig['auth_pass'] = pnsconfig['node']['password']
# It is best not use this 'httphost' in apps, and use url_of through getConfig
pnsconfig['httphost'] = 'http://' + \
    pnsconfig['node']['host']+':'+str(pnsconfig['node']['port'])
pnsconfig['mysql'] = {'host': 'ssa-mysql', 'port': 3306,
                      'user': 'root',  'password': '123456',
                      'database': 'users'}


# import user classes for server.
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
