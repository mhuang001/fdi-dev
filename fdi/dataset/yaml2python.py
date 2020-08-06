# -*- coding: utf-8 -*-
from ruamel.yaml import YAML
# import yaml
from collections import OrderedDict
import os
import sys
from string import Template
import pkg_resources
from datetime import datetime
import importlib
import pdb
# from ..pal.context import MapContext
from ..utils.options import opt
from ..utils.common import pathjoin

# a dictionary that translates metadata 'type' field to classname
from .metadata import ParameterTypes


# make simple demo for fdi
demo = 1
# if demo is true, only output this subset.
onlyInclude = ['default', 'description',
               'data_type', 'unit', 'valid', 'fits_keyword']
# only these attributes in meta
attrs = ['startDate', 'endDate', 'instrument', 'modelName', 'mission', 'type']
indent = '    '

fmtstr = {'integer': '{:d}',
          'hex': '0x{:02X}',
          'binary': '0b{:0b}',
          'float': '{:g}',
          'string': '{:s}',
          'finetime': '{:d}'
          }


def mkinfo(attrs, indent, demo, onlyInclude):
    """ make productInfo string from attributes given.

    """
    # extra indent
    ei = '    '
    indents = [ei + indent * i for i in range(5)]
    infostr = ''
    info = 'productInfo'
    infostr += indents[0] + info + ' = {\n'
    infostr += indents[1] + '\'metadata\': OrderedDict({\n'

    default_code = {}
    for met, val in attrs.items():
        # met is like 'description', 'type', 'redWinSize'
        # val is like {'data_type':'string, 'default':'foo'...}
        if met == 'creationDate':  # 'blueMode' and pname == 'valid':
            pass
        infostr += indents[2] + '\'%s\': {\n' % met
        # data_typ
        dt = val['data_type'].strip()
        # loop through the properties
        for pname, pv in val.items():
            # pname is like 'data_type', 'default'
            # pv is like 'string', 'foo, bar, and baz', '2', '(0, 0, 0,)'
            if demo and pname not in onlyInclude:
                continue
            if pname.startswith('valid'):
                if issubclass(pv.__class__, (str, bytes)):
                    s = '\'' + pv.strip() + '\''
                else:
                    lst = []
                    for k, v in pv.items():
                        if issubclass(k.__class__, tuple):
                            sk = '(' + ''.join([fmtstr[dt].format(x)
                                                + ', ' for x in k]) + ')'
                        else:
                            sk = fmtstr[dt].format(k)
                        lst += '\n' + indents[4] + \
                            sk + ': \'' + str(v)+'\','
                    kvs = ''.join(lst)
                    if len(kvs) > 0:
                        kvs += '\n' + indents[4]
                    s = '{' + kvs + '}'
            else:
                pval = pv.strip() if issubclass(pv.__class__, (str, bytes)) else str(pv)
                if pname == 'default':
                    # python instanciation source code.
                    # will be like default: FineTime1(0)
                    if dt not in ['string', 'integer', 'hex', 'binary', 'float']:
                        t = ParameterTypes[dt]
                        code = '%s(%s)' % (t, pval)
                    elif dt in ['integer', 'hex', 'float', 'binary']:
                        code = pval
                    elif pval == 'None':
                        code = 'None'
                    else:
                        code = '\'' + pval + '\''
                    default_code[met] = code
                s = '\'' + pval + '\''
            infostr += indents[3] + '\'%s\': %s,\n' % (pname, s)
        infostr += indents[2] + '},\n'
    infostr += indents[1] + '}),\n'  # 'metadata'
    infostr += indents[0] + '}\n'  # productInfo

    return infostr, default_code


def getCls(clp, rerun=True, exclude=[]):
    if clp == '':
        # classes path not goven on command line
        try:
            pc = __import__('projectclasses',
                            globals(), locals(), ['prjcls'], 0)
            print('Imported project classes from projectclasses module.')
            ret = pc.prjcls
        except ModuleNotFoundError as e:
            print('Unable to find projectclasses module. Use existing product classes.')
            ls = [(k, v) for k, v in locals().items()
                  if k not in ['clp', 'e', 'exclude', 'rerun']]
            ret = ls
    else:
        if '/' not in clp and '\\' not in clp and not clp.endswith('.py'):
            print('Importing project classes from module '+clp)
            pc = importlib.import_module(clp)
        else:
            clpp, clpf = os.path.split(clp)
            sys.path.insert(0, os.path.abspath(clpp))
            # print(sys.path)
            print('Importing project classes from file '+clp)
            pc = __import__(clpf.rsplit('.py', 1)[
                0], globals(), locals(), ['prjcls'], 0)
        ret = pc.prjcls
    return ret


def readyaml(ypath):
    """ read YAML files in ypath """
    yaml = YAML()
    desc = OrderedDict()
    for findir in os.listdir(ypath):
        fin = os.path.join(out[2]['result'], findir)

        ''' The  input file name ends with '.yaml' or '.yml' (case insensitive).
        the stem name of output file is input file name stripped of the extension.
        '''
        # make it all lower case
        finl = findir.lower()
        if finl.endswith('.yml'):
            nm = findir[:-4]
        elif finl.endswith('.yaml'):
            nm = findir[:-5]
        else:
            continue

        # read YAML
        with open(fin, 'r', encoding='utf-8') as f:
            # pyYAML d = OrderedDict(yaml.load(f, Loader=yaml.FullLoader))
            d = OrderedDict(yaml.load(f))
        attrs = OrderedDict([(x, val) for x, val in d.items()
                             if issubclass(val.__class__, dict)])
        print('Read from %s:\n%s' %
              (fin, ''.join([k + '=' + str(v) + '\n'
                             for k, v in d.items() if k not in attrs])))
        print('Find attributes:\n%s' % ''.join(
            ('%20s' % (k+'=' + str(v['default']) + ', ') for k, v in attrs.items())))
        desc[nm] = (d, attrs, fin)
    return desc


if __name__ == '__main__':

    print('product class generatiom')

    # Get input file name etc. from command line. defaut 'Product.yml'
    mdir = os.path.dirname(__file__)
    ypath = os.path.join(mdir, 'resources')
    tpath = os.path.join(mdir, 'resources')
    opath = '.'
    ops = [
        {'long': 'help', 'char': 'h', 'default': False, 'description': 'print help'},
        {'long': 'verbose', 'char': 'v', 'default': False,
         'description': 'print info'},
        {'long': 'yamldir=', 'char': 'y', 'default': ypath,
         'description': 'Input YAML file directory.'},
        {'long': 'template=', 'char': 't', 'default': tpath,
         'description': 'Product class template file directory.'},
        {'long': 'outputdir=', 'char': 'o', 'default': opath,
         'description': 'Output directory for python file.'},
        {'long': 'userclasses=', 'char': 'c', 'default': '',
         'description': 'Python file name, or a module name,  to import prjcls to update Classes with user-defined classes which YAML file refers to.'},
    ]

    out = opt(ops)
    # print([(x['long'], x['result']) for x in out])
    verbose = out[1]['result']

    ypath = out[2]['result']
    tpath = out[3]['result']
    # input file
    descriptors = readyaml(ypath)

    clp = out[5]['result']
    # include project classes for every product so that products made just
    # now can be used as parents
    from .classes import Classes
    # Do not import classes that are to be generated. Thier source code
    # could be  invalid due to unseccessful previous runs
    importexclude = list(descriptors.keys())

    for nm, daf in descriptors.items():
        d, attrs, fin = daf
        # class doc
        doc = '%s class (level %s) schema %s inheriting %s. Automatically generated from %s on %s.' % tuple(map(str, (
            d['name'], d['level'], d['schema'], d['parent'],
            fin, datetime.now())))

        Classes.makePackageClasses(rerun=True, exclude=importexclude)
        Classes.updateMapping(getCls(clp, rerun=True, exclude=importexclude))
        glb = Classes.mapping

        # the generated source code must import these
        seen = []
        imports = 'from collections import OrderedDict\n'
        # import parent class
        pn = d['parent']
        if pn and pn != '':
            a = pn  # TODO: multiple parents
            s = 'from %s import %s\n' % (glb[a].__module__, a)
            if a not in seen:
                seen.append(a)
                imports += s

            # get parent attributes
            all_attrs = glb[a].productInfo['metadata']
            # merge to get all attributes including parents' and self's.
            all_attrs.update(attrs)
        else:
            all_attrs = attrs

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
        opath = os.path.abspath(out[4]['result'])
        fout = pathjoin(opath, d['name'].lower()+'.py')
        print("Output python file is "+fout)

        # make aubatitution dictionary for Template
        subs = {}
        subs['WARNING'] = '# Automatically generated from %s. Do not edit.' % fin
        subs['PRODUCTNAME'] = d['name']
        print('product name: %s' % subs['PRODUCTNAME'])
        subs['PARENT'] = pn if pn and pn != '' else ''
        print('parent class: %s' % subs['PARENT'])
        subs['IMPORTS'] = imports
        print('import class: %s' % seen)
        subs['CLASSDOC'] = doc
        subs['PROJECTINFO'] = infs
        subs['INITARGS'] = ikwds
        print('productInfo=\n%s\n' % (subs['INITARGS']))

        # subtitute the template
        with open(os.path.join(tpath, d['name'] + '.template')) as f:
            t = f.read()

        sp = Template(t).safe_substitute(subs)
        # print(sp)
        with open(fout, 'w') as f:
            f.write(sp)

        # import the newly made class  so the following classes could use it
        prodname = d['name']
        if prodname not in glb and prodname not in importexclude:
            # absolute import from opath. The new products cannot do relative import
            sys.path.insert(0, opath)
            try:
                _o = importlib.import_module(prodname.lower(), '')
                glb[prodname] = getattr(_o, prodname)
                print('Imported fresh ' + prodname + ' from '+opath)
            except Exception as e:
                print('Unable to import fresh ' + prodname +
                      ' from '+opath + '.')
                raise(e)
        # the next product can use this one.
        importlib.invalidate_caches()
        importexclude.remove(prodname)
