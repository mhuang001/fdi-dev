# -*- coding: utf-8 -*-
from os.path import join
import logging
import getpass
import os
from os.path import expanduser, expandvars

pnsconfig = dict()

###########################################
# Configuration for Servers running locally.
# components of the default poolurl

# the key (variable names) must be uppercased for Flask server
# FLASK_CONF = pnsconfig

# To be edited automatically with sed -i 's/^EXTHOST =.*$/EXTHOST = xxx/g' file
EXTUSER = ''
EXTPASS = ''
EXTHOST = '172.17.0.1'
EXTPORT = 9876
EXTRO_USER = ''
EXTRO_PASS = ''
SELF_HOST = '172.17.0.2'
SELF_PORT = 9876
SELF_USER = 'fdi'
SELF_PASS = ''
MQUSER = ''
MQPASS = ''
MQHOST = '172.17.0.1'
MQPORT = 9876

BASE_LOCAL_POOLPATH = '/tmp'
SERVER_POOLPATH = '/tmp/data'

SCHEME = 'http'
API_VERSION = 'v0.14'
API_BASE = '/fdi'

pnsconfig['server_scheme'] = 'server'

pnsconfig['cloud_token'] = '/tmp/.cloud_token'
pnsconfig['cloud_username'] = 'mh'
pnsconfig['cloud_password'] = 'G44G898g'
pnsconfig['cloud_host'] = '123.56.102.90'
pnsconfig['cloud_port'] = 31702

pnsconfig['cloud_scheme'] = 'csdb'
pnsconfig['cloud_api_version'] = 'v1'
pnsconfig['cloud_api_base'] = '/csdb'
pnsconfig['cloud_baseurl'] = pnsconfig['cloud_api_base'] + \
    '/' + pnsconfig['cloud_api_version']

LOGGER_LEVEL = logging.INFO

# base url for webserver. Update version if needed.
pnsconfig['scheme'] = SCHEME
pnsconfig['api_version'] = API_VERSION
pnsconfig['api_base'] = API_BASE
pnsconfig['baseurl'] = API_BASE + '/' + API_VERSION

# look-up table for PoolManager (therefor HttpClient) to get pool URLs eith Pool ID (poolname)
poolurl_of = {
    'e2e10': 'http://10.0.10.114:9885'+pnsconfig['baseurl']+'/e2e',
    'e2e5k': 'http://127.0.0.1:5000'+pnsconfig['baseurl']+'/e2e',
    'e2e127': 'http://127.0.0.1:9885'+pnsconfig['baseurl']+'/e2e',
}
pnsconfig['lookup'] = poolurl_of

# base url for pool, you must have permission of this path, for example : /home/user/Documents
# this base pool path will be added at the beginning of your pool urn when you init a pool like:
# pstore = PoolManager.getPool('/demopool_user'), it will create a pool at /data.demopool_user/
# User can disable  basepoolpath by: pstore = PoolManager.getPool('/demopool_user', use_default_poolpath=False)
pnsconfig['base_local_poolpath'] = BASE_LOCAL_POOLPATH
pnsconfig['server_poolpath'] = SERVER_POOLPATH  # For server
pnsconfig['defaultpool'] = 'default'
pnsconfig['loggerlevel'] = LOGGER_LEVEL

# choose from pre-defined.
conf = ['dev', 'external', 'production', 'public'][0]

# modify
if conf == 'dev':
    # username, passwd, flask ip, flask port
    pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                         'host': '0.0.0.0', 'port': 9885,
                         'ro_username': 'poolrw', 'rw_password': 'k/p=0',
                         'ro_username': 'poolro', 'ro_password': 'only5%',
                         }

    # server permission user
    pnsconfig['base_local_poolpath'] = '/tmp'
    pnsconfig['server_poolpath'] = '/tmp/data'  # For server
    # server's own
    pnsconfig['self_host'] = pnsconfig['node']['host']
    pnsconfig['self_port'] = pnsconfig['node']['port']
    pnsconfig['self_username'] = pnsconfig['node']['username']
    pnsconfig['self_password'] = pnsconfig['node']['password']
    # PTS app permission user
    pnsconfig['ptsuser'] = 'mh'
    # on pns server
    home = '/home/' + pnsconfig['ptsuser']
elif conf == 'external':
    # wsgi behind apach2. cannot use env vars
    pnsconfig['node'] = {'username': EXTUSER, 'password': EXTPASS,
                         'host': EXTHOST, 'port': EXTPORT,
                         'ro_username': EXTRO_USER, 'ro_password': EXTRO_PASS,
                         }
    pnsconfig['server_poolpath'] = SERVER_POOLPATH  # For server
    # server's own
    pnsconfig['self_host'] = SELF_HOST
    pnsconfig['self_port'] = SELF_PORT
    pnsconfig['self_username'] = SELF_USER
    pnsconfig['self_password'] = SELF_PASS
    # PTS app permission user
    pnsconfig['ptsuser'] = 'pns'
    # on pns server
    home = '/home/' + pnsconfig['ptsuser']
elif conf == 'production':
    pnsconfig['node'] = {'username': 'fdi', 'password': 'bar',
                         'host': '10.0.10.114', 'port': 9885,
                         'ro_username': 'ro', 'ro_password': '',
                         }
    # server's own
    pnsconfig['self_host'] = pnsconfig['node']['host']
    pnsconfig['self_port'] = pnsconfig['node']['port']
    pnsconfig['self_username'] = pnsconfig['node']['username']
    pnsconfig['self_password'] = pnsconfig['node']['password']
    # PTS app permission user
    pnsconfig['ptsuser'] = 'pns'
    # on pns server
    home = '/home/' + pnsconfig['ptsuser']
elif conf == 'public':
    pnsconfig['node'] = {'username': 'rw', 'password': 'only6%',
                         'host': '123.56.102.90', 'port': 31702,
                         'ro_username': 'ro', 'ro_password': 'only5%',
                         }
    # server's own
    pnsconfig['self_host'] = pnsconfig['node']['host']
    pnsconfig['self_port'] = pnsconfig['node']['port']
    pnsconfig['self_username'] = pnsconfig['node']['username']
    pnsconfig['self_password'] = pnsconfig['node']['password']
    # PTS app permission user
    pnsconfig['ptsuser'] = 'pns'
    # on pns server
    home = '/home/' + pnsconfig['ptsuser']
else:
    pass

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

############## project specifig ####################
# message queue config
pnsconfig['mqtt'] = dict(
    host='0.0.0.0',
    port=31876,
    username='foo',
    passwd='bar',
)

# OSS config
pnsconfig['oss'] = dict(
    access_key_id=os.getenv('OSS_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('OSS_ACCESS_KEY_SECRET'),
    bucket_name=os.getenv('OSS_BUCKET'),
    endpoint=os.getenv('OSS_ENDPOINT'),
)
