# -*- coding: utf-8 -*-
from os.path import join


# base url for webserver
pnsconfig = dict(baseurl='/v0.6')

dev = False
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
    pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                         'host': '10.0.10.114', 'port': 9888}
    # server permission user
    pnsconfig['serveruser'] = 'apache'
    # PTS app permission user
    pnsconfig['ptsuser'] = 'pns'
    # on server
    home = '/root'


phome = join(home, 'pns')
pnsconfig['paths'] = dict(
    pnshome=phome,
    inputdir=join(phome, 'input'),
    inputfiles=['infile'],
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
