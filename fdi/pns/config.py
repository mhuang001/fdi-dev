# -*- coding: utf-8 -*-

import os
import logging


# with prefix
pnsconfig = {}
# without prefix
config = {}

###########################################
# Configuration for Servers running locally.

# the key (variable names) must be uppercased for Flask server
# FLASK_CONF = pnsconfig

pnsconfig['server_scheme'] = 'server'

pnsconfig['logger_level'] = logging.INFO
pnsconfig['logger_level_extras'] = logging.WARNING

# base url for webserver.
pnsconfig['scheme'] = 'http'
pnsconfig['api_version'] = 'v0.15'  # vx.yy
pnsconfig['baseurl'] = '/fdi/v0.15'  # fdi/vx.yy

""" base url for the pool, you must have permission of this path, for example : /home/user/Documents
# This local base pool path will be added at the beginning of your pool urn when you init a pool like:

.. :code:
  pstore = PoolManager.getPool('/demopool_user')

It will create a pool at /data/demopool_user/
# User can disable  basepoolpath by:

.. :code:

  pstore = PoolManager.getPool('/demopool_user', use_default_poolpath=False)

"""

# For server. If needed for test_pal this should point to a locally
# writeable dir. If needed to change for a server, do it with
# an environment var.
pnsconfig['base_local_poolpath'] = '/tmp/httppool'
pnsconfig['server_local_poolpath'] = pnsconfig['base_local_poolpath'] + '/data'
pnsconfig['defaultpool'] = 'default'

# choose from pre-defined profiles. 'production' is for making docker image.
conf = ['dev', 'production'][1]
# https://requests.readthedocs.io/en/latest/user/advanced/?highlight=keep%20alive#timeouts
pnsconfig['requests_timeout'] = (3.3, 909)

# modify
if conf == 'dev':
    # username, passwd, flask ip, flask port.
    # For test clients. the username/password must match rw
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
    pnsconfig['rw_user'] = 'foo'
    pnsconfig['rw_pass'] = 'pbkdf2:sha256:260000$V1hXW8OVUKekaSHP$85b21f4fb0a3c6f0eef73165538d7aab7881ce8acc48c4af59fd33edd8bf13f2'

    pnsconfig['ro_user'] = 'bar'
    pnsconfig['ro_pass'] = 'pbkdf2:sha256:260000$8vrAxZeeJJhTrZLQ$70fd3819d62bb46fe89fc1cd933fb8052e83da75d66624b6146f105288be0bfd'

elif conf == 'production':
    pnsconfig['username'] = 'foo'
    pnsconfig['password'] = 'bar'
    pnsconfig['host'] = '111.111.111.111'
    pnsconfig['port'] = 2222

    pnsconfig['self_host'] = '0.0.0.0'
    pnsconfig['self_port'] = 9876
    pnsconfig['self_username'] = 'fdi'
    pnsconfig['self_password'] = 'ONLY_IF_NEEDED'
    # For server. needed for test_pal so this should point to a locally
    # writeable dir. If needed to change for a server, do it with
    # an environment var.
    pnsconfig['base_local_poolpath'] = '/tmp/httppool'
    pnsconfig['server_local_poolpath'] = pnsconfig['base_local_poolpath'] + '/data'

    pnsconfig['rw_user'] = 'foo'
    pnsconfig['rw_pass'] = 'pbkdf2:sha256:260000$V1hXW8OVUKekaSHP$85b21f4fb0a3c6f0eef73165538d7aab7881ce8acc48c4af59fd33edd8bf13f2'
    pnsconfig['ro_user'] = 'bar'
    pnsconfig['ro_pass'] = 'pbkdf2:sha256:260000$8vrAxZeeJJhTrZLQ$70fd3819d62bb46fe89fc1cd933fb8052e83da75d66624b6146f105288be0bfd'

    # (reverse) proxy_fix
    # pnsconfig['proxy_fix'] = dict(x_for=1, x_proto=1, x_host=1, x_prefix=1)

else:
    pass

# import user classes for server.
# See document in :class:`Classes`
pnsconfig['userclasses'] = ''

############## project specific ####################
pnsconfig['docker_version'] = ''
pnsconfig['server_version'] = ''

pnsconfig['cloud_token'] = '/tmp/.cloud_token'
pnsconfig['cloud_username'] = 'mh'
pnsconfig['cloud_password'] = ''
pnsconfig['cloud_host'] = ''
pnsconfig['cloud_port'] = 31702

pnsconfig['cloud_scheme'] = 'csdb'
pnsconfig['cloud_api_version'] = 'v1'
pnsconfig['cloud_api_base'] = '/csdb'

# message queue config
pnsconfig.update(dict(
    mq_host='172.17.0.1',
    mq_port=9876,
    mq_user='',
    mq_pass='',
))

# pipeline config
pnsconfig.update(dict(
    pipeline_host='172.17.0.1',
    pipeline_port=9876,
    pipeline_user='',
    pipeline_pass='',
))

# OSS config
pnsconfig.update(dict(
    oss_access_key_id=None,
    oss_access_key_secret=None,
    oss_bucket_name=None,
    oss_endpoint=None,
    oss_prefix=None
))
