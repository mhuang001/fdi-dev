# -*- coding: utf-8 -*-
from os.path import join


# base url for webserver
pnsconfig = dict(baseurl='/v0.6')

# username, passwd, flask ip, flask port
pnsconfig['node'] = {'username': 'foo', 'password': 'bar',
                     'host': '0.0.0.0', 'port': 5000}

# input file
# output file
from os.path import expanduser, expandvars
home = expanduser(expandvars('$HOME'))
# apache wsgi will return '$HOME' with no expansion
home = '/root' if home == '$HOME' else home
phome = join(home, 'pns')
pnsconfig['paths'] = dict(
    pnshome=phome,
    inputdir=join(phome, 'input'),
    inputfiles=['infile'],
    outputdir=join(phome, 'output'),
    outputfile='outfile'
)

# the stateless data processing program that reads from inputdir and
# leave the output in the outputdir. The format is the input for subprocess()
h = pnsconfig['paths']['pnshome']
pnsconfig['scripts'] = dict(
    init=[join(h, 'initPTS'), ''],
    config=[join(h, 'configPTS'), ''],
    prog=[join(h, 'runPTS'), ''],
    clean=[join(h, 'cleanPTS'), '']
)
del phome, h

# seconds
pnsconfig['timeout'] = 10

# server permission user
pnsconfig['serveruser'] = 'apache'
