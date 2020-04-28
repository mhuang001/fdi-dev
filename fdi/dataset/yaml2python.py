# -*- coding: utf-8 -*-
import yaml
from collections import OrderedDict
import os
from string import Template
import pkg_resources
import pdb
# from ..pal.context import MapContext
from ..utils.options import opt


# a dictionary that translates metadata 'type' field to classname
from fdi.dataset.metadata import ParameterTypes
from .deserialize import makedesables

glb = makedesables()


# make simple demo for fdi
demo = 1
# if demo is true, only output this subset.
onlyInclude = ['default', 'description', 'data_type', 'unit']
# only these attributes in meta
attrs = ['startDate', 'endDate', 'instrument', 'modelName', 'mission', 'type']
indent = '    '


def mkinfo(d, attrs, indent, demo, onlyInclude):
    # extra indent
    ei = '    '
    infostr = ''
    if d['CSCLEVEL'] == 'ALL':
        info = 'productInfo' if d['name'] == 'BaseProduct' else 'projectInfo'
    else:
        info = 'info'
    infostr += ei + info + ' = {\n'
    infostr += ei + indent + '\'metadata\': {\n'

    default = {}
    for met, val in attrs.items():
        infostr += ei + indent * 2 + '\'%s\': {\n' % met
        # loop through the properties
        for pname, pval in val.items():
            if demo and pname not in onlyInclude:
                continue
            dt = val['data_type'].strip()
            if pname == 'default' and dt != 'string':
                # python instanciation source code.
                # will be like default: FineTime1(0)
                t = ParameterTypes[dt]
                s = '%s(%s)' % (t, pval.strip())
            else:
                s = '\'' + pval.strip() + '\''
            infostr += ei + indent * 3 + '\'%s\': %s,\n' % (pname, s)
            if pname == 'default':
                default[met] = s
        infostr += ei + indent * 2 + '},\n'
    infostr += ei + indent + '},\n'
    infostr += ei + '}\n'

    return infostr, info, default


if __name__ == '__main__':

    print('product class generatiom')

    # Get input file name etc. from command line. defaut 'Product.yml'
    mdir = os.path.dirname(__file__)
    ydir = os.path.join(mdir, 'resources', pkg_resources.resource_filename(
        'fdi.dataset.resources', 'Product.yml'))
    tdir = os.path.join(mdir, 'resources', pkg_resources.resource_filename(
        'fdi.dataset.resources', 'Product.template'))
    ops = [
        {'long': 'help', 'char': 'h', 'default': False, 'description': 'print help'},
        {'long': 'verbose', 'char': 'v', 'default': False,
         'description': 'print info'},
        {'long': 'yamlfile=', 'char': 'y', 'default': ydir,
         'description': 'Input file name.'},
        {'long': 'template=', 'char': 't', 'default': tdir,
         'description': 'Product class template file name.'},
        {'long': 'outputdir', 'char': 'o', 'default': '.',
         'description': 'Output directory for python file.'},
    ]
    # pdb.set_trace()
    out = opt(ops)
    # print([(x['long'], x['result']) for x in out])
    verbose = out[1]['result']

    fin = out[2]['result']

    '''' if input file name ends with '.yaml' or '.yml' (case insensitive)
    the stem name of output file is input file name stripped of the extension, else the
    stem is the input file name's.
    '''
    # make it all lower case
    finl = fin.lower()
    if finl.endswith('.yml'):
        nm = fin[:-4]
    else:
        nm = fin[:-5] if finl.endswith('.yaml') else fin

    # read YAML
    with open(fin, 'r') as f:
        d = OrderedDict(yaml.load(f, Loader=yaml.FullLoader))
    attrs = OrderedDict([(x, val) for x, val in d.items()
                         if issubclass(val.__class__, dict)])
    print('Read from %s:\n%s' %
          (fin, ''.join([k+'='+v+'\n' for k, v in d.items() if k not in attrs])))
    print('Find attributes:\n%s' % ''.join(
        ('%20s' % (k+'=' + v['default'] + ', ') for k, v in attrs.items())))

    # make output filename. by default is in YAML input file "name" + .py
    fout = pathjoin(out[4]['result'], d['name'].lower())

    # make metadata dictionary
    # inf = projectinfo/info
    infs, inf, default = mkinfo(d, attrs, indent, demo, onlyInclude)

    # the generated source code must import these
    seen = []
    imports = '# import datetime\n'
    for met, val in attrs.items():
        a = ParameterTypes[val['data_type']]
        if a in glb:
            # this attribute class has module
            s = 'from %s import %s' % (glb[a].__module__, a)
            if a not in seen:
                seen.append(a)
                imports += s+'\n'

    # import parent class
    a = ParameterTypes[d['parent']]
    s = 'from %s import %s' % (glb[a].__module__, a)
    if a not in seen:
        seen.append(a)
        imports += s

    # keyword argument for __init__
    ls = [' '*17 + '%s = %s,\n' %
          (x + '_' if x == 'type' else x, default[x]) for x in attrs]
    ikwds = ''.join(ls).strip('\n')
    # make aubatitution dictionary for Template
    subs = {}
    subs['WARNING'] = '# Automatically generated from %s. Do not edit.' % fin
    subs['PRODUCTNAME'] = d['name']
    print('product name: %s' % subs['PRODUCTNAME'])
    subs['PARENT'] = ParameterTypes[d['parent']]
    print('parent class: %s' % subs['PARENT'])
    subs['IMPORTS'] = imports + '\n'
    print('import class:\n%s' % seen)
    subs['PROJECTINFO'] = infs+'\n'
    subs['INF'] = inf
    subs['INITARGS'] = ikwds
    print('%s:\n%s\n' % (subs['INF'], subs['INITARGS']))

    # subtitute the template
    with open(out[3]['result']) as f:
        t = f.read()

    sp = Template(t).safe_substitute(subs)
    # print(sp)
    with open(fout, 'w') as f:
        f.write(sp)
