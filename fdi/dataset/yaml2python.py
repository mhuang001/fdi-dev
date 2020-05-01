# -*- coding: utf-8 -*-
import yaml
from collections import OrderedDict
import os
from string import Template
import pkg_resources
from datetime import datetime
import pdb
# from ..pal.context import MapContext
from ..utils.options import opt
from ..utils.common import pathjoin

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


def mkinfo(attrs, indent, demo, onlyInclude):
    # extra indent
    ei = '    '
    infostr = ''
    info = 'productInfo'
    infostr += ei + info + ' = {\n'
    infostr += ei + indent + '\'metadata\': OrderedDict({\n'

    default_code = {}
    for met, val in attrs.items():
        # met is like 'description', 'type', 'redWinSize'
        # val is like {'data_type':'string, 'default':'foo'...}
        infostr += ei + indent * 2 + '\'%s\': {\n' % met
        # loop through the properties
        for pname, pv in val.items():
            # pname is like 'data_type', 'default'
            # pv is like 'string', 'foo, bar, and baz', '2', '(0, 0, 0,)'
            if demo and pname not in onlyInclude:
                continue
            dt = val['data_type'].strip()
            pval = pv.strip()
            if pname == 'default':
                # python instanciation source code.
                # will be like default: FineTime1(0)
                if dt not in ['string', 'integer', 'hex', 'float']:
                    t = ParameterTypes[dt]
                    code = '%s(%s)' % (t, pval)
                elif dt in ['integer', 'hex', 'float'] or pval == 'None':
                    code = pval
                else:
                    code = '\'' + pval + '\''
                default_code[met] = code
            s = '\'' + pval + '\''
            infostr += ei + indent * 3 + '\'%s\': %s,\n' % (pname, s)
        infostr += ei + indent * 2 + '},\n'
    infostr += ei + indent + '}),\n'  # 'metadata'
    infostr += ei + '}\n'  # productInfo

    return infostr, default_code


if __name__ == '__main__':

    print('product class generatiom')

    # Get input file name etc. from command line. defaut 'Product.yml'
    mdir = os.path.dirname(__file__)
    ypath = os.path.join(mdir, 'resources', pkg_resources.resource_filename(
        'fdi.dataset.resources', 'Product.yml'))
    tpath = os.path.join(mdir, 'resources', pkg_resources.resource_filename(
        'fdi.dataset.resources', 'Product.template'))
    ops = [
        {'long': 'help', 'char': 'h', 'default': False, 'description': 'print help'},
        {'long': 'verbose', 'char': 'v', 'default': False,
         'description': 'print info'},
        {'long': 'yamlfile=', 'char': 'y', 'default': ypath,
         'description': 'Input file path.'},
        {'long': 'template=', 'char': 't', 'default': tpath,
         'description': 'Product class template file path.'},
        {'long': 'outputdir=', 'char': 'o', 'default': '.',
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

    # class doc
    doc = '%s class (level %s) version %s inheriting %s. Automatically generated from %s on %s.' % (
        d['name'], d['CSCLEVEL'], d['version'], d['parent'], fin, str(datetime.now()))

    # the generated source code must import these
    seen = []
    imports = 'from collections import OrderedDict\n'
    # import parent class
    a = ParameterTypes[d['parent']]  # TODO: multiple parents
    s = 'from %s import %s\n' % (glb[a].__module__, a)
    if a not in seen:
        seen.append(a)
        imports += s

    # get parent attributes
    all_attrs = glb[a]().productInfo['metadata']
    # merge to get all attributes including parents' and self's.
    all_attrs.update(attrs)

    for met, val in all_attrs.items():
        a = ParameterTypes[val['data_type']]
        if a in glb:
            # this attribute class has module
            s = 'from %s import %s' % (glb[a].__module__, a)
            if a not in seen:
                seen.append(a)
                imports += s+'\n'

    # make metadata dictionary
    infs, default_code = mkinfo(all_attrs, indent, demo, onlyInclude)

    # keyword argument for __init__
    ls = [' '*17 + '%s = %s,\n' %
          (x + '_' if x == 'type' else x, default_code[x]) for x in all_attrs]
    ikwds = ''.join(ls).strip('\n')

    # make output filename. by default is in YAML input file "name" + .py
    fout = pathjoin(out[4]['result'], d['name'].lower()+'.py')
    print("Output python file is "+fout)

    # make aubatitution dictionary for Template
    subs = {}
    subs['WARNING'] = '# Automatically generated from %s. Do not edit.' % fin
    subs['PRODUCTNAME'] = d['name']
    print('product name: %s' % subs['PRODUCTNAME'])
    subs['PARENT'] = ParameterTypes[d['parent']]
    print('parent class: %s' % subs['PARENT'])
    subs['IMPORTS'] = imports + '\n'
    print('import class: %s' % seen)
    subs['CLASSDOC'] = doc
    subs['PROJECTINFO'] = infs+'\n'
    subs['INITARGS'] = ikwds
    print('productInfo=\n%s\n' % (subs['INITARGS']))

    # subtitute the template
    with open(out[3]['result']) as f:
        t = f.read()

    sp = Template(t).safe_substitute(subs)
    # print(sp)
    with open(fout, 'w') as f:
        f.write(sp)
