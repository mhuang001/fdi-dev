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

# from ..pal.context import MapContext
from ..utils.options import opt
from ..utils.common import pathjoin, trbk
from ..utils.ydump import ydump
from ..utils.moduleloader import SelectiveMetaFinder, installSelectiveMetaFinder

# a dictionary that translates metadata 'type' field to classname
from .metadata import ParameterTypes, ParameterDataTypes

import logging

# create logger
logger = logging.getLogger(__file__)
logging.basicConfig(stream=sys.stdout,
                    format='%(asctime)s - %(levelname)7s'
                           ' - [%(filename)s:%(lineno)3s'
                           ' - %(funcName)10s()] - %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger().setLevel(logging.DEBUG)


installSelectiveMetaFinder()

# make simple demo for fdi
demo = 0
# if demo is true, only output this subset.
onlyInclude = ['default', 'description',
               'data_type', 'unit', 'valid', 'fits_keyword']
# only these attributes in meta
attrs = ['startDate', 'endDate', 'instrument', 'modelName', 'mission', 'type']
indent = '    '
# extra indent
ei = ''
indents = [ei + indent * i for i in range(10)]

fmtstr = {
    'integer': '{:d}',
    'short': '{:d}',
    'hex': '0x{:02X}',
    'byte': '{:d}',
    'binary': '0b{:0b}',
    'float': '{:g}',
    'string': '"{:s}"',
    'finetime': '{:d}'
}


def mkinfo(metas, dsets, indents):
    """ make productInfo string from metadata and dataset strings given.

    """
    infostr = ''
    info = 'productInfo'
    infostr += indents[0] + info + ' = {\n'
    infostr += metas
    infostr += dsets
    infostr += indents[0] + '}\n'  # productInfo
    return infostr


def getPython(val, indents, demo, onlyInclude):
    """ make productInfo and init__() code strings from given data.
    """
    infostr = ''

    if issubclass(val.__class__, dict):
        infostr += '{\n'
        code = {}
        for k, v in val.items():
            sk = str(k)
            infostr += indents[0] + '"""%s""": ' % sk
            if issubclass(v.__class__, dict) and 'data_type' in v:
                # v is a dict of parameters
                istr, d_code = params(v, indents[1:], demo, onlyInclude)
            else:
                istr, d_code = getPython(v, indents[1:], demo, onlyInclude)
            infostr += istr
            code[sk] = d_code
        infostr += indents[0] + '},\n'
    elif issubclass(val.__class__, list):
        infostr += '[\n'
        code = []
        for v in val:
            infostr += indents[0]
            if issubclass(v.__class__, dict) and 'data_type' in v:
                # val is a list of column (and 'data' in x )
                istr, d_code = params(v, indents[1:], demo, onlyInclude)
            else:
                istr, d_code = getPython(v, indents[1:], demo, onlyInclude)
            infostr += istr
            code.append(d_code)
        infostr += indents[0] + '],\n'
    else:
        pval = '"""' + val + \
            '"""' if issubclass(val.__class__, (str, bytes)) else str(val)
        infostr += pval + ',\n'
        code = pval
    return infostr, code


def makeinitcode(dt, pval):
    """ python instanciation source code.

    will be like "default: FineTime1(0)"
    """
    if dt not in ['string', 'integer', 'hex', 'binary', 'float']:
        # custom classes
        t = ParameterTypes[dt]
        code = '%s(%s)' % (t, pval)
    elif dt in ['integer', 'hex', 'float', 'binary']:
        code = pval
    elif pval == 'None':
        code = 'None'
    else:
        code = '"""' + pval + '"""'
    return code


def params(val, indents, demo, onlyInclude):
    """ generates python strng for val, a parameter with a set of attribute

    see getPython
    """
    infostr = '{\n'
    code = None
    # data_type
    dt = val['data_type'].strip()
    # loop through the properties
    for pname, pv in val.items():
        # pname is like 'data_type', 'default'
        # pv is like 'string', 'foo, bar, and baz', '2', '(0, 0, 0,)'
        if demo and pname not in onlyInclude:
            continue
        if pname.startswith('valid'):
            if pv is None:
                pv = ''

            if issubclass(pv.__class__, (str, bytes)):
                s = '"""' + pv.strip() + '"""'
            else:
                lst = []
                for k, v in pv.items():
                    if issubclass(k.__class__, tuple):
                        fs = fmtstr[dt]
                        # (,999) in yaml is ('',999) but None from inhrited class
                        foo = [fs.format(x) if x != '' and x is not None else 'None'
                               for x in k]
                        sk = '(' + ', '.join(foo) + ')'
                    else:
                        sk = fmtstr[dt].format(k)
                    lst += '\n' + indents[2] + \
                        sk + ': """' + str(v)+'""",'
                kvs = ''.join(lst)
                if len(kvs) > 0:
                    kvs += '\n' + indents[2]
                s = '{' + kvs + '}'
        else:
            iss = issubclass(pv.__class__, (str))

            # get string representation
            pval = str(pv).strip() if iss else str(pv)
            if pname == 'default':
                code = makeinitcode(dt, pval)
            if pname in ['example', 'default']:
                # here data_type instead of input type determines the output type
                iss = val['data_type'] == 'string'
            s = '"""' + pval + '"""' if iss else pval
        infostr += indents[1] + '"""%s""": %s,\n' % (pname, s)
    infostr += indents[1] + '},\n'

    return infostr, code


def getCls(clp, rerun=True, exclude=None, verbose=False):
    if exclude is None:
        exclude = []
    if clp == '':
        # classes path not given on command line
        try:
            pc = importlib.import_module('svom.products.projectclasses')
            pc.PC.updateMapping(rerun=rerun, exclude=exclude, verbose=verbose)
            ret = pc.PC.mapping
            print(
                'Imported project classes from svom.products.projectclasses module.')
        except (ModuleNotFoundError, SyntaxError) as e:
            print('!'*80 +
                  '\nUnable to import svom.products.projectclasses module.\n' +
                  '!'*80+'\n'+str(e)+'\n'+'!'*80)
            ls = []
            # ls = [(k, v) for k, v in locals().items()
            #      if k not in ['clp', 'e', 'exclude', 'rerun']]
            ret = ls
            # print(e)
            # print(trbk(e))
            # raise
    else:
        if '/' not in clp and '\\' not in clp and not clp.endswith('.py'):
            print('Importing project classes from module '+clp)
            pc = importlib.import_module(clp)
        else:
            clpp, clpf = os.path.split(clp)
            sys.path.insert(0, os.path.abspath(clpp))
            # print(sys.path)
            print('Importing project classes from file '+clp)
            pc = importlib.import_module(clpf.replace('.py', ''))
        pc.PC.updateMapping(rerun=rerun, exclude=exclude)
        ret = pc.PC.mapping
    return ret


def readyaml(ypath, ver=None):
    """ read YAML files in ypath.

    output: nm is  stem of file name. desc is descriptor, key being yaml[name]
    """
    yaml = YAML()
    desc = OrderedDict()
    fins = {}
    for findir in os.listdir(ypath):
        fin = os.path.join(ypath, findir)

        ''' The  input file name ends with '.yaml' or '.yml' (case insensitive).
        the stem name of output file is input file name stripped of the extension.
        '''
        # make it all lower case
        finl = findir.lower()
        if finl.endswith('.yml') or finl.endswith('.yaml'):
            nm = os.path.splitext(findir)[0]
        else:
            continue
        fins[nm] = fin

        # read YAML
        print('----- Reading ' + fin + '-----')
        with open(fin, 'r', encoding='utf-8') as f:
            # pyYAML d = OrderedDict(yaml.load(f, Loader=yaml.FullLoader))
            d = OrderedDict(yaml.load(f))

        if float(d['schema']) >= 1.0:
            pass
            print('Read %s from %s' % (d['schema'], fin))
        if float(d['schema']) > 0.6:
            attrs = OrderedDict(d['metadata'])
            datasets = OrderedDict()
            # move primary level table to datasets
            if 'TABLE' in attrs:
                datasets['TABLE'] = {}
                datasets['TABLE']['TABLE'] = attrs['TABLE']
                del attrs['TABLE']
            if 'datasets' in d:
                datasets.update(d['datasets'])
            print('Read from %s:\n%s' %
                  (fin, ''.join([k + '=' + str(v) + '\n'
                                 for k, v in d.items() if k not in ['metadata', 'datasets']])))

            print('Find attributes:\n%s' %
                  ''.join(('%20s' % (k+'=' + str(v['default'])
                                     if 'default' in v else 'url' + ', ')
                           for k, v in attrs.items()
                           )))
            if float(d['schema']) > 1.1:
                itr = ('%20s' % (k+'=' + str([c for c in (v['TABLE'] if 'TABLE'
                                                          in v else [])]))
                       for k, v in datasets.items())
                print('Find datasets:\n%s' % ', '.join(itr))
            else:
                # v1.1 1.0 0.7
                itr = ('%20s' %
                       (k+'=' + str([c['name'] for c in (v['TABLE'] if 'TABLE'
                                                         in v else [])]))
                       for k, v in datasets.items())
                print('Find datasets:\n%s' % ', '.join(itr))
            desc[d['name']] = (d, attrs, datasets, fin)
        else:
            # float(d['schema']) <= 0.6:
            d2 = OrderedDict()
            metadata = OrderedDict()
            for k, v in d.items():
                if issubclass(v.__class__, dict):
                    if v['unit'] == 'None':
                        dt = v['data_type']
                        if dt in ['boolean', 'string']:
                            v['unit'] = None
                    metadata[k] = v
                else:
                    if k == 'definition':
                        d2['description'] = v
                    elif k == 'schema':
                        d2[k] = version
                    elif k == 'parent':
                        d2['parents'] = [v]
                    else:
                        d2[k] = v
            d2['metadata'] = metadata
            desc[d['name']] = d2
    return desc, fins


def output(nm, d, fins, version, verbose):

    print("Input YAML file is to be renamed to " + fins[nm]+'.old')
    fout = fins[nm]
    print("Output YAML file is "+fout)
    if 0:
        ydump(d, sys.stdout)  # yamlfile)
    else:
        os.rename(fins[nm], fins[nm]+'.old')
        with open(fout, 'w', encoding='utf-8') as yamlfile:
            ydump(d,  yamlfile)


def yamlupgrade(descriptors, fins, ypath, version, verbose):

    if float(version) > 1.0:
        for nm, daf in descriptors.items():
            d, attrs, datasets, fin = daf
            if float(d['schema']) >= float(version):
                print('No need to upgrade '+d['schema'])
                continue
            d['schema'] = version
            for pname, w in d['metadata'].items():
                dt = w['data_type']
                # no dataset yet
                if dt in ['boolean', 'string', 'finetime']:
                    del w['unit']
                if dt == 'finetime':
                    w['default'] = 0
                if 'typecode' not in w:
                    w['typecode'] = 'B' if dt == 'string' else None
                if pname == 'version':
                    v = w['default'].replace('v', '')
                    w['default'] = str(float(v) + 0.1)
            output(nm, d, fins, version, verbose)
    elif float(version) > 0.6:
        # in:v0.6 and below out:v1.0
        for nm, d in descriptors.items():
            output(nm, d, fins, version, verbose)


def removeParent(a, b):
    if a == b:
        print('%s and %s are the same class' % (b, a))
        return None
    tmp = "remove parent %s because it is another parent %s's"
    if issubclass(glb[a], glb[b]):
        # remove b
        print(tmp % (b, a))
        return b
    elif issubclass(glb[b], glb[a]):
        # remove a
        print(tmp % (a, b))
        return a
    else:
        return None


def noParentsParents(pn):
    removed = []
    for i in range(len(pn)-1):
        if pn[i] in removed:
            continue
        for j in range(i+1, len(pn)):
            r = removeParent(pn[i], pn[j])
            if r:
                removed.append(r)
            if r == pn[i]:
                break
    for r in removed:
        pn.remove(r)
    return pn


if __name__ == '__main__':

    print('product class generatiom')

    # schema version
    version = '1.1'

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
        {'long': 'upgrade', 'char': 'u', 'default': False,
         'description': 'Upgrade the file to current schema, to a filename + ' + version},
        {'long': 'debug', 'char': 'd', 'default': False,
         'description': 'run in pdb. type "c" to continuue.'},
    ]

    out = opt(ops)
    # print([(x['long'], x['result']) for x in out])
    verbose = out[1]['result']
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    ypath = out[2]['result']
    tpath = out[3]['result']
    upgrade = out[6]['result']
    debug = out[7]['result']
    project_class_path = out[5]['result']

    if debug:
        import pdb
        pdb.set_trace()

    # input file
    descriptors, fins = readyaml(ypath, version)
    if upgrade:
        yamlupgrade(descriptors, fins, ypath, version, verbose)
        sys.exit()

    # include project classes for every product so that products made just
    # now can be used as parents
    from .classes import Classes

    # Do not import modules that are to be generated. Thier source code
    # could be  invalid due to unseccessful previous runs
    importexclude = [x.lower() for x in descriptors.keys()]

    pcl = getCls(project_class_path, rerun=True,
                 exclude=importexclude, verbose=verbose)
    Classes.updateMapping(
        c=pcl, rerun=True, exclude=importexclude, verbose=verbose)
    glb = Classes.mapping

    for nm, daf in descriptors.items():
        d, attrs, datasets, fin = daf
        print('************** Processing ' + nm + '***********')
        prodname = d['name']
        # module/output-file name is YAML input file "name" with lowercase
        modulename = nm.lower()

        # make output filename, lowercase modulename + .py
        opath = os.path.abspath(out[4]['result'])
        fout = pathjoin(opath, modulename + '.py')
        print("Output python file is "+fout)

        # class doc
        doc = '%s class (level %s) schema %s inheriting %s. Automatically generated from %s on %s.' % tuple(map(str, (
            prodname, d['level'], d['schema'], d['parents'],
            fin, datetime.now())))

        # the generated source code must import these
        seen = []
        imports = 'from collections import OrderedDict\n'
        # import parent classes
        pn = d['parents']
        # remove classes that are other's parent class (MRO problem)
        if pn and len(pn):
            pn = noParentsParents(pn)

        if pn and len(pn):
            all_attrs = OrderedDict()
            for a in pn:
                if a is None:
                    continue
                modnm = glb[a].__module__
                s = 'from %s import %s\n' % (modnm, a)
                if a not in seen:
                    seen.append(a)
                    imports += s

                # get parent attributes
                mod = sys.modules[modnm]
                all_attrs.update(mod.ProductInfo['metadata'])
            # merge to get all attributes including parents' and self's.
            all_attrs.update(attrs)
        else:
            all_attrs = attrs

        # parameter classes used in init code may need to be imported, too
        for met, val in all_attrs.items():
            a = ParameterTypes[val['data_type']]
            if a in glb:
                # this attribute class has module
                s = 'from %s import %s' % (glb[a].__module__, a)
                if a not in seen:
                    seen.append(a)
                    imports += s+'\n'

        # make metadata and dataset dictionaries
        d['metadata'] = all_attrs
        d['datasets'] = datasets
        infs, default_code = getPython(d, indents[1:], demo, onlyInclude)
        # remove the ',' at the end.
        infostr = (ei + 'ProductInfo = ' + infs).strip()[:-1]

        # keyword argument for __init__
        ls = []
        for x in all_attrs:
            arg = x + '_' if x == 'type' else x
            val = default_code['metadata'][x]
            ls.append(' '*17 + '%s = %s,\n' % (arg, val))

        ikwds = ''.join(ls).strip('\n')

        # make substitution dictionary for Template
        subs = {}
        subs['WARNING'] = '# Automatically generated from %s. Do not edit.' % fin
        subs['PRODUCTNAME'] = prodname
        print('product name: %s' % subs['PRODUCTNAME'])
        subs['PARENTS'] = ''.join(
            [c+',' for c in pn if c]) if pn and len(pn) else ''
        print('parent class: %s' % subs['PARENTS'])
        subs['IMPORTS'] = imports
        print('import class: %s' % seen)
        subs['CLASSDOC'] = doc
        subs['PRODUCTINFO'] = infostr
        subs['INITARGS'] = ikwds
        print('productInit=\n%s\n' % (subs['INITARGS']))

        # subtitute the template
        if os.path.exists(os.path.join(tpath, prodname + '.template')):
            tname = os.path.join(tpath, prodname + '.template')
        elif os.path.exists(os.path.join(tpath, 'template')):
            tname = os.path.join(tpath, 'template')
        else:
            logger.error('Template file not found.')
            sys.exit(-3)
        with open(tname, encoding='utf-8') as f:
            t = f.read()

        sp = Template(t).safe_substitute(subs)
        # print(sp)
        with open(fout, 'w', encoding='utf-8') as f:
            f.write(sp)

        # import the newly made module  so the following classes could use it
        # if all((modulename not in m.split('.') for m in Classes.modclass)):

            # absolute import from opath. The new products cannot do relative import
        if opath not in sys.path:
            sys.path.insert(0, opath)
        if 0:
            newp = 'fresh ' + prodname + ' from ' + modulename + ' in ' + opath + '.'
            try:
                _o = importlib.import_module(modulename)
                glb[prodname] = getattr(_o, prodname)
                print('Imported ' + newp)
            except Exception as e:
                print('Unable to import ' + newp)
                raise(e)
        # the next product can use this one.
        importlib.invalidate_caches()
        importexclude.remove(modulename)
        pcl = getCls(project_class_path, rerun=True, exclude=importexclude)
        Classes.updateMapping(c=pcl, rerun=True, exclude=importexclude)
        glb = Classes.mapping
