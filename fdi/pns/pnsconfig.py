# -*- coding: utf-8 -*-
from os.path import join
import logging
import getpass
import pwd

# logging level for server or possibly by client
pnsconfig = dict(logginglevel=logging.INFO)

# base url for webserver. Update version if needed.
pnsconfig['baseurl'] = '/v0.6'

dev = True
if dev:
    # username, passwd, flask ip, flask port
    pnsconfig['node'] = {'username': 'foo',
                         'password': 'bar', 'host': '0.0.0.0', 'port': 5000}

    # server permission user. default is current user
    pnsconfig['serveruser'] = getpass.getuser()
    # PTS app permission user. default is pnsconfig['serveruser']
    pnsconfig['ptsuser'] = pnsconfig['serveruser']
    # the directory where the pns ome is on server. default is ptsuser home
    home = pwd.getpwnam(pnsconfig['ptsuser']).pw_dir
else:
    pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                         'host': '10.0.10.114', 'port': 9888}
    # server permission user. Change this according to local setup. e.g. 'apache'
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
