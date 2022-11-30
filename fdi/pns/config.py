# -*- coding: utf-8 -*-

import os
from os.path import join
import logging
import getpass

pnsconfig = {}

###########################################
# Configuration for Servers running locally.

# the key (variable names) must be uppercased for Flask server
# FLASK_CONF = pnsconfig

pnsconfig['server_scheme'] = 'server'

pnsconfig['logger_level'] = logging.INFO
pnsconfig['logger_level_extras'] = logging.WARNING

# base url for webserver.
pnsconfig['scheme'] = 'http'
pnsconfig['api_version'] = 'v0.15'  # vx.yyy
pnsconfig['api_base'] = '/fdi'        # /fdi
pnsconfig['baseurl'] = pnsconfig['api_base'] + \
    '/' + pnsconfig['api_version']  # /fdi/vx.yyy

""" base url for the pool, you must have permission of this path, for example : /home/user/Documents
# This local base pool path will be added at the beginning of your pool urn when you init a pool like:

.. :code:
  pstore = PoolManager.getPool('/demopool_user')

It will create a pool at /data/demopool_user/
# User can disable  basepoolpath by:

.. :code:

  pstore = PoolManager.getPool('/demopool_user', use_default_poolpath=False)

"""

pnsconfig['server_local_poolpath'] = '/tmp/data'
pnsconfig['defaultpool'] = 'default'

# choose from pre-defined profiles. 'production' is for making docker image.
conf = ['dev', 'production'][1]
# https://requests.readthedocs.io/en/latest/user/advanced/?highlight=keep%20alive#timeouts
pnsconfig['requests_timeout'] = (3.3, 909)

# modify
if conf == 'dev':
    # username, passwd, flask ip, flask port.
    # For test clients. the username/password must match ['USERS'][0]
    pnsconfig['username'] = 'foo'
    pnsconfig['password'] = 'bar'
    pnsconfig['host'] = '127.0.0.1'
    pnsconfig['port'] = 9885

    # server's own in the context of its os/fs/globals
    pnsconfig['self_host'] = pnsconfig['host']
    pnsconfig['self_port'] = pnsconfig['port']
    pnsconfig['self_username'] = 'USERNAME'
    pnsconfig['self_password'] = 'ONLY_IF_NEEDED'
    pnsconfig['base_local_poolpath'] = '/tmp'
    pnsconfig['server_local_poolpath'] = '/tmp/data'  # For server

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

    # (reverse) proxy_fix
    # /pnsconfig['proxy_fix'] = dict(x_for=1, x_proto=1, x_host=1, x_prefix=1)
elif conf == 'production':
    pnsconfig['username'] = 'foo'
    pnsconfig['password'] = 'bar'
    pnsconfig['host'] = '127.0.0.1'
    pnsconfig['port'] = 9876

    pnsconfig['self_host'] = '172.17.0.2'
    pnsconfig['self_port'] = 9876
    pnsconfig['self_username'] = 'fdi'
    pnsconfig['self_password'] = 'ONLY_IF_NEEDED'
    # For server. needed for test_pal so this should point to a locally
    # writeable dir. If needed to change for a server, do it with
    # an environment var.
    pnsconfig['base_local_poolpath'] = '/tmp/httppool'
    pnsconfig['server_local_poolpath'] = pnsconfig['base_local_poolpath'] + '/data'

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

else:
    pass

# import user classes for server.
# See document in :class:`Classes`
pnsconfig['userclasses'] = ''

pnsconfig['poolurl'] = ''.join((pnsconfig['scheme'], '://',
                                pnsconfig['host'], ':',
                                str(pnsconfig['port']),
                                pnsconfig['baseurl']
                                ))

############## project specific ####################
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

# message queue config
pnsconfig.update(dict(
    mqhost='172.17.0.1',
    mqport=9876,
    mquser='',
    mqpass='',
))

# pipeline config
pnsconfig.update(dict(
    pipelinehost='172.17.0.1',
    pipelineport=9876,
    pipelineuser='',
    pipelinepass='',
))

# OSS config
pnsconfig['oss'] = dict(
    access_key_id=None,
    access_key_secret=None,
    bucket_name=None,
    endpoint=None,
    prefix=None
)
