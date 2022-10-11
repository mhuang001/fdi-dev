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
MQHOST = '172.17.0.1'
MQPORT = 9876
MQUSER = ''
MQPASS = ''
PIPELINEHOST = '172.17.0.1'
PIPELINEPORT = 9876
PIPELINEUSER = ''
PIPELINEPASS = ''

BASE_LOCAL_POOLPATH = '/tmp'
SERVER_POOLPATH = '/tmp/data'

SCHEME = 'http'
API_VERSION = 'v0.15'
API_BASE = '/fdi'

pnsconfig['server_scheme'] = 'server'

pnsconfig['cloud_token'] = '/tmp/.cloud_token'
pnsconfig['cloud_username'] = 'mh'
pnsconfig['cloud_password'] = ''
pnsconfig['cloud_host'] = ''
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
conf = ['dev', 'external', 'production'][0]

# modify
if conf == 'dev':
    # username, passwd, flask ip, flask port.
    # For server these are for clients,
    # for a client this is server access info.
    pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                         'host': '0.0.0.0', 'port': 9885,
                         }

    # server's own in the context of its os/fs/globals
    pnsconfig['self_host'] = pnsconfig['node']['host']
    pnsconfig['self_port'] = pnsconfig['node']['port']
    pnsconfig['self_username'] = pnsconfig['node']['username']
    pnsconfig['self_password'] = pnsconfig['node']['password']
    pnsconfig['base_local_poolpath'] = '/tmp'
    pnsconfig['server_poolpath'] = '/tmp/data'  # For server
    pnsconfig['POOL_DATABASE'] = pnsconfig['server_poolpath'] + '/pool.db'
    # In place of a frozen user DB for backend server and test.
    pnsconfig['USERS'] = [
        {'username': 'foo',
         'hashed_password': 'pbkdf2:sha256:260000$Ch0GEGjA6ipF3dOb$3d408b50a31c64de75d8973e8aebaf76a510cfb01c9af03a1294bac792fe9608',
         'roles': ('read_write',)
         },
        {'username': 'ro',
         'hashed_password': 'pbkdf2:sha256:260000$gzsbbunF2NQb5okJ$0ef0a27f7f6802d0394214df638c739d2bb0a5c4091ac7d4273fd236ca77ee3f',
         'roles': ('read_only',)
         }
    ]

    # PTS app permission user
    pnsconfig['ptsuser'] = 'mh'
    # on pns server
    home = '/home/' + pnsconfig['ptsuser']
elif conf == 'external':
    # wsgi behind apach2. cannot use env vars
    pnsconfig['node'] = {'username': EXTUSER, 'password': EXTPASS,
                         'host': EXTHOST, 'port': EXTPORT,
                         }
    pnsconfig['server_poolpath'] = SERVER_POOLPATH  # For server
    # server's own in the context of its os/fs/globals
    pnsconfig['self_host'] = SELF_HOST
    pnsconfig['self_port'] = SELF_PORT
    pnsconfig['self_username'] = SELF_USER
    pnsconfig['self_password'] = SELF_PASS

    # In place of a frozen user DB for backend server and test.
    pnsconfig['USERS'] = [
        {'username': EXTUSER,
         'hashed_password': EXTPASS,
         'roles': ['read_write']
         },
        {'username': EXTRO_USER,
         'hashed_password': EXTRO_PASS,
         'roles': ['read_only']
         }
    ]

    # (reverse) proxy_fix
    pnsconfig['proxy_fix'] = dict(x_for=1, x_proto=1, x_host=1, x_prefix=1)
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

############## project specific ####################
# message queue config
pnsconfig.update(dict(
    mqhost=MQHOST,
    mqport=MQPORT,
    mquser=MQUSER,
    mqpass=MQPASS,
))

# pipeline config
pnsconfig.update(dict(
    pipelinehost=PIPELINEHOST,
    pipelineport=PIPELINEPORT,
    pipelineuser=PIPELINEUSER,
    pipelinepass=PIPELINEPASS,
))

# OSS config
pnsconfig['oss'] = dict(
    access_key_id=None,
    access_key_secret=None,
    bucket_name=None,
    endpoint=None,
    prefix=None
)
