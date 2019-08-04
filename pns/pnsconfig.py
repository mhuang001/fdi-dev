# -*- coding: utf-8 -*-
from os.path import join
# base url for webserver
baseurl = '/v0.4'

# username, passwd, flask ip, flask port
node = {'username': 'foo', 'password': 'bar',
        'host': '0.0.0.0', 'port': 5000}

# input file
# output file
paths = dict(
    pnshome='/tmp/pns',
    inputdir='/tmp/input',
    inputfiles=['infile'],
    outputdir='/tmp/output',
    outputfile='outfile'
)
# the stateless data processing program that reads from inputdir and
# leave the output in the outputdir. The format is the input for subprocess()
init = [join(paths['pnshome'], 'initPTS'), '']
config = [join(paths['pnshome'], 'configPTS'), '']
prog = [join(paths['pnshome'], 'hello'), '']
clean = [join(paths['pnshome'], 'cleanPTS'), '']

# seconds
timeout = 10
