
# base url for webserver
baseurl = '/v0.4'

# username, passwd, flask ip, flask port
node = {'username': 'foo', 'password': 'bar',
        'host': '10.0.10.108', 'port': 8900}

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
init = [paths['pnshome'] + '/initPTS', '']
config = [paths['pnshome'] + '/configPTS', '']
prog = [paths['pnshome'] + '/hello', '']
clean = [paths['pnshome'] + '/cleanPTS', '']
