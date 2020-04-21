# -*- coding: utf-8 -*-
import yaml
import collections
import pprint


# make simple demo for fdi
demo = 1
indent = '    '

nm = 'Mandatory'
fin = nm + '.yml'

# a dictionary that translates metadata 'type' field to python instanciation source code.
instanciation = {
    'string': '\'%s\'',
    'finetime1': 'FineTime1(%s)'
}
imports = '#import datetime\n' +\
    'from fdi.dataset.finetime import FineTime1\n'

with open(fin, 'r') as f:
    d = collections.OrderedDict(yaml.load(f))

fout = d['name'] + 'Info.py'

with open(fout, 'w') as f:
    print('# -*- coding: utf-8 -*-\n\n' +
          '# Automatically generated from %s. Do not edit.\n\n' % fin +
          imports + '\n' +
          'info = {\n' +
          indent + '\'metadata\': {',
          file=f)
    for met, val in d.items():
        if met in ['name', 'CSCLEVEL', 'version']:
            #print(indent*2+'\'%s\': \'%s\'' % (met, val.strip()), file=f)
            pass
        else:
            print(indent * 2 + '\'%s\': {' % met, file=f)
            # loop through the properties
            for pname, pval in val.items():
                if demo and pname not in ['default', 'description', 'data_type']:
                    continue
                if pname == 'default':
                    s = instanciation[val['data_type'].strip()] % pval.strip()
                else:
                    s = '\'' + pval.strip() + '\''
                print(indent * 3 + '\'%s\': %s,' % (pname, s), file=f)
            print(indent * 2 + '},', file=f)
    print(indent + '},', file=f)
    print('}', file=f)
