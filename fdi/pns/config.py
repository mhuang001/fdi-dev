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
# session activity debugging
pnsconfig['ses_dbg'] = 0

# base url for webserver.
pnsconfig['scheme'] = 'http'
pnsconfig['api_version'] = 'v0.17'  # vx.yy
pnsconfig['baseurl'] = '/fdi/v0.17'  # fdi/vx.yy

# For server. If needed for test_pal so this should point to a locally
# writeable dir. If needed to change for a server, do it with
# an environment var. Ref `PoolManager.PlacePaths`.
pnsconfig['base_local_poolpath'] = '/tmp/data'
pnsconfig['server_local_poolpath'] = os.path.join(
    pnsconfig['base_local_poolpath'],
    pnsconfig['api_version'])
pnsconfig['cookie_file'] = os.path.join(
    os.path.expanduser("~"), '.config', 'cookies.txt')

# choose from pre-defined profiles. 'production' is for making docker image.
conf = ['dev', 'production'][1]
# https://requests.readthedocs.io/en/latest/user/advanced/?highlight=keep%20alive#timeouts
pnsconfig['requests_timeout'] = (0.3, 10)

# nominal username, passwd, flask ip, flask port.
# For test clients. the username/password must match rw
pnsconfig['username'] = 'foo'
pnsconfig['password'] = 'bar'
pnsconfig['host'] = 'localhost' #'127.0.0.1'
pnsconfig['port'] = 9885
# a dictionary of poolname - poolurl pairs
pnsconfig['read_only_pools'] = {
    'test_e2e2_vt':'csdb://123.56.102.90:31702/csdb/v1/storage/test_e2e2_vt'}

# modify
if conf == 'dev':
    # In place of a frozen user DB for backend server and test.
    # **** CHANGE rw/ro_... values on production deployment
    pnsconfig['rw_user'] = pnsconfig['username']
    pnsconfig['rw_pass'] = 'pbkdf2:sha256:260000$CMSfHEQMBKrIRbUx$2ecb5bb7d64b0b554238194046531612898ef28eef2d870d45309a91fceae655'

    pnsconfig['ro_user'] = pnsconfig['password']
    pnsconfig['ro_pass'] = 'pbkdf2:sha256:260000$8vrAxZeeJJhTrZLQ$70fd3819d62bb46fe89fc1cd933fb8052e83da75d66624b6146f105288be0bfd'

    pnsconfig['admin_user'] = None
    pnsconfig['admin_pass'] = None

    # server's own in the context of its os/fs/globals
    pnsconfig['self_host'] = pnsconfig['host']
    pnsconfig['self_port'] = pnsconfig['port']

    # provide OS login and pass if login the server or interact as a user.
    pnsconfig['self_username'] = 'USERNAME'
    pnsconfig['self_password'] = 'ONLY_IF_NEEDED'
    pnsconfig['base_local_poolpath'] = '/tmp'
    # For server. needed for test_pal so this should point to a locally
    # writeable dir. If needed to change for a server, do it with
    # an environment var.
    pnsconfig['server_local_poolpath'] = '/tmp/data'  # For server

elif conf == 'production':
    pnsconfig['rw_user'] = 'foo'
    pnsconfig['rw_pass'] = 'pbkdf2:sha256:260000$V1hXW8OVUKekaSHP$85b21f4fb0a3c6f0eef73165538d7aab7881ce8acc48c4af59fd33edd8bf13f2'
    pnsconfig['ro_user'] = 'bar'
    pnsconfig['ro_pass'] = 'pbkdf2:sha256:260000$8vrAxZeeJJhTrZLQ$70fd3819d62bb46fe89fc1cd933fb8052e83da75d66624b6146f105288be0bfd'

    # For server. needed for test_pal so this should point to a locally
    # writeable dir. If needed to change for a server, do it with
    # an environment var.
    pnsconfig['baseurl'] = '/fdi/v0.17'

    pnsconfig['self_host'] = '0.0.0.0'
    pnsconfig['self_port'] = 9876
    pnsconfig['self_username'] = 'fdi'
    pnsconfig['self_password'] = 'ONLY_IF_NEEDED'

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

pnsconfig['cloud_token'] = 'TO BE FILLED'
pnsconfig['cloud_user'] = 'mh'
pnsconfig['cloud_pass'] = ''
pnsconfig['cloud_host'] = ''
pnsconfig['cloud_port'] = 31702

pnsconfig['cloud_scheme'] = 'csdb'
pnsconfig['cloud_api_version'] = 'v1'
pnsconfig['cloud_api_base'] = '/csdb'

# aliases for `getConfig('poolurl:[key]')
pnsconfig['url_aliases'] = {'http': pnsconfig['scheme'] + \
    '://' + pnsconfig['host'] + ':' + str(pnsconfig['port']) + \
    pnsconfig['baseurl']}

# message queue config
pnsconfig.update(dict(
    mq_host='172.17.0.1',
    mq_port=9876,
    mq_user='',
    mq_pass='',
))

# OSS config
pnsconfig.update(dict(
    oss_access_key_id=None,
    oss_access_key_secret=None,
    oss_bucket_name=None,
    oss_endpoint=None,
    oss_prefix=None
))
