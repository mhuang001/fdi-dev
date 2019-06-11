
# base url for webserver
baseurl = '/v0.1'

# username, passwd, flask ip, flask port
node = {'username': 'foo', 'password': 'bar', 'host': '0.0.0.0', 'port': 5000}

# input file
inputfile = '/tmp/input/infile'

# output file
outputfile = '/tmp/output/outfile'

# the stateless data processing program that reads from inputdir and
# leave the output in the outputdir. The format is the input for subprocess()
prog = ['/tmp/hello', '']
