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
from .attributable import make_class_properties
# a dictionary that translates metadata 'type' field to classname
from .datatypes import DataTypes, DataTypeNames

import logging

# create logger
logger = logging.getLogger(__file__)
logging.basicConfig(stream=sys.stdout,
                    format='%(asctime)s -%(levelname)4s'
                           ' -[%(filename)s:%(lineno)3s'
                           ' -%(funcName)10s()] - %(message)s',
                    datefmt="%Y%m%d %H:%M:%S")
logging.getLogger().setLevel(logging.DEBUG)


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


def sq(s):
    """ add quote mark to string, depending on if ' or " in the string.
    """

    if "'" in s or '\n' in s:
        qm = '"""' if '"' in s or '\n' in s else '"'
    else:
        qm = "'"
    return '%s%s%s' % (qm, s, qm)


def getPython(val, indents, demo, onlyInclude, debug=False):
    """ make Model and init__() code strings from given data.
    """
    infostr = ''

    if issubclass(val.__class__, dict):
        infostr += '{\n'
        code = {}
        for k, v in val.items():
            if debug:
                logger.info('KWD[%s]=%s' %
                            (str(k), '...' if k == 'metadata' else str(v)))
            sk = str(k)
            infostr += '%s%s: ' % (indents[0], sq(sk))
            if issubclass(v.__class__, dict) and 'default' in v:
                # as in k:v
                # k:
                #   data_type: string
                #   description: Description of this dataset
                #   default: UNKNOWN
                #   valid: ''
                # v is a dict of parameter attributes
                istr, d_code = params(
                    v, indents[1:], demo, onlyInclude, debug=debug)
            else:
                # headers such as name, parents, schema metadata...
                istr, d_code = getPython(
                    v, indents[1:], demo, onlyInclude, debug=debug)
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
                istr, d_code = params(
                    v, indents[1:], demo, onlyInclude, debug=debug)
            else:
                istr, d_code = getPython(
                    v, indents[1:], demo, onlyInclude, debug=debug)
            infostr += istr
            code.append(d_code)
        infostr += indents[0] + '],\n'
    else:
        pval = sq(val) if issubclass(val.__class__, (str, bytes)) else str(val)
        infostr += pval + ',\n'
        code = pval
    return infostr, code


def makeinitcode(dt, pval):
    """ python instanciation source code.

    will be like "default: FineTime1(0)"
    """
    if dt not in ['string', 'integer', 'hex', 'binary', 'float']:
        # custom classes
        t = DataTypes[dt]
        code = '%s(%s)' % (t, pval)
    elif dt in ['integer', 'hex', 'float', 'binary']:
        code = pval
    elif pval == 'None':
        code = 'None'
    else:
        code = sq(pval)
    return code


def params(val, indents, demo, onlyInclude, debug=False):
    """ generates python strng for val, a parameter with a set of attribute

    val: as in ```name:val```
    ```
    nam:
        data_type: string
        description: Description of this dataset
        default: UNKNOWN
        valid: ''
    ```
    see getPython
    """

    # output string of the data model
    modelString = '{\n'
    # source code for init kwds.
    code = None

    # data_type
    dt = val['data_type'].strip()
    # loop through the properties
    for pname, pv in val.items():
        # pname is like 'data_type', 'default'
        # pv is like 'string', 'foo, bar, and baz', '2', '(0, 0, 0,)'
        if demo and pname not in onlyInclude:
            continue
        if debug:
            logger.info('val[%s]=%s' % (str(pname), str(pv)))
        if pname.startswith('valid'):
            if pv is None:
                pv = ''

            if issubclass(pv.__class__, (str, bytes)):
                s = sq(pv.strip())
            else:
                # e.g. {(5,66):'fooo'}
                lst = []
                for k, v in pv.items():
                    if issubclass(k.__class__, tuple):
                        fs = fmtstr[dt]
                        # (,999) in yaml is ('',999) but None from inhrited class
                        foo = [fs.format(x) if x != '' and x is not None else 'None'
                               for x in k]
                        sk = '(' + ', '.join(foo) + ')'
                    else:
                        if debug:
                            logger.info('%s: data_type %s format %s' %
                                        (pname, dt, k))
                        try:
                            sk = fmtstr[dt].format(k)
                        except TypeError:
                            sk = '# Bad format string for %s: %s. Ignored.' % (
                                dt, k)
                            logger.warning(sk)
                    lst += '\n' + '%s%s: %s,' % (indents[2], sk, sq(str(v)))
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
                iss = (val['data_type'] == 'string') and (pval != 'None')
            s = sq(pval) if iss else pval
        modelString += indents[1] + '%s: %s,\n' % (sq(pname), s)
    modelString += indents[1] + '},\n'

    return modelString, code


def getCls(clp, rerun=True, exclude=None, verbose=False):
    if clp is None or len(clp.strip()) == 0:
        return {}
    if exclude is None:
        exclude = []
    if '/' not in clp and '\\' not in clp and not clp.endswith('.py'):
        print('Importing project classes from module '+clp)
        # classes path not given on command line
        pc = importlib.import_module(clp)
        pc.PC.updateMapping(rerun=rerun, exclude=exclude,
                            verbose=verbose, ignore_error=True)
        ret = pc.PC.mapping
        print(
            'Imported project classes from svom.products.projectclasses module.')

    else:
        clpp, clpf = os.path.split(clp)
        sys.path.insert(0, os.path.abspath(clpp))
        # print(sys.path)
        print('Importing project classes from file '+clp)
        pc = importlib.import_module(clpf.replace('.py', ''))
        sys.path.pop(0)
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
        if 'metadata' not in d or d['metadata'] is None:
            d['metadata'] = {}
        if 'datasets' not in d or d['datasets'] is None:
            d['datasets'] = {}
        if float(d['schema']) >= 1.0:
            pass
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
            print('Pre-emble:\n%s' %
                  (''.join([k + '=' + str(v) + '\n'
                            for k, v in d.items() if k not in ['metadata', 'datasets']])))

            logger.debug('Find attributes:\n%s' %
                         ''.join(('%20s' % (k+'=' + str(v['default'])
                                            if 'default' in v else 'url' + ', ')
                                  for k, v in attrs.items()
                                  )))
            if float(d['schema']) > 1.1:
                itr = ('%20s' % (k+'=' + str([c for c in (v['TABLE'] if 'TABLE'
                                                          in v else [])]))
                       for k, v in datasets.items())
                logger.debug('Find datasets:\n%s' % ', '.join(itr))
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

    if float(version) == 1.6:
        for nm, daf in descriptors.items():
            d, attrs, datasets, fin = daf
            if float(d['schema']) >= float(version):
                print('No need to upgrade '+d['schema'])
                continue
            d['schema'] = version
            level = d.pop('level')
            md = OrderedDict()
            for pname, w in d['metadata'].items():
                #dt = w['data_type']
                # no dataset yet
                if pname == 'type':
                    v = w['default']
                    w.clear()
                    w['default'] = v
                    md[pname] = w
                    md['level'] = {'default': 'C' + level.upper()}
                elif pname == 'FORMATV':
                    v = w['default'].split('.')
                    w.clear()
                    w['default'] = version + '.' + \
                        v[2] + '.' + str(int(v[3])+1)
                    md[pname] = w
                else:
                    md[pname] = w
            d['metadata'] = md
            if 'datasets' not in d:
                d['datasets'] = {}
            output(nm, d, fins, version, verbose)


def dependency_sort(descriptors):
    """ sort the descriptors so that everyone's parents are to his right.

    """
    ret = []
    # make a list of prodcts
    working_list = list(descriptors.keys())
    while len(working_list):
        # examin one by one
        # must use index to loop
        for i in range(len(working_list)):
            # find parents of i
            nm = working_list[i]
            p = descriptors[nm][0]['parents']
            nm_found_parent = False
            if len(p) == 0:
                continue
            found = set(working_list) & set(p)
            # for x in working_list:
            #    if x == nm:
            #        continue
            #    if x in p:
            if len(found):
                # parent is in working_list
                working_list.remove(nm)
                working_list.append(nm)
                nm_found_parent = True
                break
            else:
                # no one in the list is nm's superclass
                # TODO: only immediate parenthood tested
                ret.append(nm)
                working_list.remove(nm)
                break
            if nm_found_parent:
                break
        else:
            # no one in the list is free from deendency to others
            if len(working_list):
                msg = 'Cyclic dependency among ' + str(working_list)
                logger.error(msg)
                sys.exit(-5)
    return ret


def removeParent(a, b):
    """ Returns the one who is the other one's parent.
    """
    if a == b:
        logger.debug('%s and %s are the same class' % (b, a))
        return None
    tmp = "remove parent %s because it is another parent %s's"
    if issubclass(glb[a], glb[b]):
        # remove b
        logger.debug(tmp % (b, a))
        return b
    elif issubclass(glb[b], glb[a]):
        # remove a
        logger.debug(tmp % (a, b))
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
    version = '1.6'

    # Get input file name etc. from command line. defaut 'Product.yml'
    cwd = os.path.abspath(os.getcwd())
    ypath = cwd
    tpath = cwd
    opath = cwd
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
        {'long': 'packagename=', 'char': 'p', 'default': '-',
         'description': 'Name of the package which the generated modules belong to.'},
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
    opath = os.path.abspath(out[4]['result'])
    package_name = out[5]['result']
    project_class_path = out[6]['result']
    upgrade = out[7]['result']
    debug = out[8]['result']

    if debug:
        import pdb
        pdb.set_trace()

    # input file
    descriptors, fins = readyaml(ypath, version)
    if upgrade:
        yamlupgrade(descriptors, fins, ypath, version, verbose)
        sys.exit()

    if package_name == '-':
        ao = os.path.abspath(opath)
        if not ao.startswith(cwd):
            logger.error('Cannot derive package name from yaml dir and cwd.')
            exit(-3)
        package_name = ao[len(cwd):].strip('/').replace('/', '.')
    logger.debug("Package name: " + package_name)

    # Do not import modules that are to be generated. Thier source code
    # could be  invalid due to unseccessful previous runs
    importexclude = [x.lower() for x in descriptors.keys()]
    importinclude = {}

    # activate a module loader that refuses to load excluded
    installSelectiveMetaFinder()

    # include project classes for every product so that products made just
    # now can be used as parents
    from .classes import Classes
    pcl = getCls(project_class_path, rerun=True,
                 exclude=importexclude, verbose=verbose)
    glb = Classes.updateMapping(
        c=pcl, rerun=True, exclude=importexclude, verbose=verbose)
    # make a list whose members do not depend members behind
    sorted_list = dependency_sort(descriptors)
    for nm in sorted_list:
        d, attrs, datasets, fin = descriptors[nm]
        print('************** Processing ' + nm + '***********')

        modelName = d['name']
        # module/output file name is YAML input file "name" with lowercase
        modulename = nm.lower()

        # schema
        schema = d['schema']

        # the generated source code must import these
        seen = []
        imports = 'from collections import OrderedDict\n'
        # import parent classes
        parentNames = d['parents']
        # remove classes that are other's parent class (MRO problem)
        if parentNames and len(parentNames):
            parentNames = noParentsParents(parentNames)

        if parentNames and len(parentNames):
            includingParentsAttributes = OrderedDict()
            for parent in parentNames:
                if parent is None:
                    continue
                modnm = glb[parent].__module__
                s = 'from %s import %s\n' % (modnm, parent)
                if parent not in seen:
                    seen.append(parent)
                    imports += s

                # get parent attributes
                mod = sys.modules[modnm]
                if hasattr(mod, '_Model_Spec'):
                    includingParentsAttributes.update(
                        mod._Model_Spec['metadata'])
            # merge to get all attributes including parents' and self's.
            toremove = []
            for nam, val in attrs.items():
                if float(schema) > 1.5 and 'data_type' not in val:
                    # update parent's
                    includingParentsAttributes[nam].update(attrs[nam])
                    toremove.append(nam)
                else:
                    # override
                    includingParentsAttributes[nam] = attrs[nam]
            for nam in toremove:
                del attrs[nam]
        else:
            includingParentsAttributes = attrs

        # make output filename, lowercase modulename + .py
        fout = pathjoin(opath, modulename + '.py')
        print("Output python file is "+fout)

        # class doc
        doc = '%s class schema %s inheriting %s.\n\nAutomatically generated from %s on %s.\n\nDescription:\n%s' % tuple(map(str, (
            modelName, schema, d['parents'],
            fin, datetime.now(), d['description'])))

        # parameter classes used in init code may need to be imported, too
        for met, val in includingParentsAttributes.items():
            a = DataTypes[val['data_type']]
            if a in glb:
                # this attribute class has module
                s = 'from %s import %s' % (glb[a].__module__, a)
                if a not in seen:
                    seen.append(a)
                    imports += s+'\n'

        # make metadata and dataset dicts
        d['metadata'] = includingParentsAttributes
        d['datasets'] = datasets
        infs, default_code = getPython(d, indents[1:], demo, onlyInclude)
        # remove the ',' at the end.
        modelString = (ei + '_Model_Spec = ' + infs).strip()[:-1]

        # keyword argument for __init__
        ls = []
        for x in includingParentsAttributes:
            arg = 'typ_' if x == 'type' else x
            val = default_code['metadata'][x]
            ls.append(' '*17 + '%s = %s,' % (arg, val))
        ikwds = '\n'.join(ls)

        # make class properties
        properties = make_class_properties(attrs)

        # make substitution dictionary for Template
        subs = {}
        subs['WARNING'] = '# Automatically generated from %s. Do not edit.' % fin
        subs['MODELNAME'] = modelName
        print('product name: %s' % subs['MODELNAME'])
        subs['PARENTS'] = ', '.join(c for c in parentNames if c)
        print('parent class: %s' % subs['PARENTS'])
        subs['IMPORTS'] = imports
        print('import class: %s' % seen)
        subs['CLASSDOC'] = doc
        subs['MODELSPEC'] = modelString
        subs['INITARGS'] = ikwds
        print('%s=\n%s\n' % ('Model Initialization', subs['INITARGS']))
        subs['PROPERTIES'] = properties

        # subtitute the template
        if os.path.exists(os.path.join(tpath, modelName + '.template')):
            tname = os.path.join(tpath, modelName + '.template')
        elif os.path.exists(os.path.join(tpath, 'template')):
            tname = os.path.join(tpath, 'template')
        else:
            logger.error('Template file not found in %s for %s.' %
                         (tpath, modelName))
            sys.exit(-3)
        with open(tname, encoding='utf-8') as f:
            t = f.read()

        sp = Template(t).safe_substitute(subs)
        # print(sp)
        with open(fout, 'w', encoding='utf-8') as f:
            f.write(sp)
        print('Done saving ' + fout + '\n' + '='*40)

        # import the newly made module to test and, for class generatiom, so the following classes could use it
        importexclude.remove(modulename)
        # importlib.invalidate_caches()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
        newp = 'fresh ' + modelName + ' from ' + modulename + \
            '.py of package ' + package_name + ' in ' + opath + '.'
        if modelName.endswith('_DataModel'):
            # the target is `Model`
            continue
        # If the last segment of package_name happens to be a module name in
        # exclude list the following import will be blocked. So lift
        # exclusion temporarily
        exclude_save = importexclude[:]
        importexclude.clear()
        try:
            _o = importlib.import_module(
                package_name + '.' + modulename, package_name)
            glb[modelName] = getattr(_o, modelName)
        except Exception as e:
            print('Unable to import ' + newp)
            raise(e)
        importexclude.extend(exclude_save)
        print('Imported ' + newp)
        # Instantiate and dump metadata in text format
        prod = glb[modelName]()
        fg = {'name': 15, 'value': 18, 'unit': 7, 'type': 8,
              'valid': 26, 'default': 18, 'code': 4, 'description': 25}
        sp = prod.meta.toString(tablefmt='fancy_grid', param_widths=fg)

        mout = pathjoin(ypath, modelName + '.txt')
        with open(mout, 'w', encoding='utf-8') as f:
            f.write(sp)
        print('Done dumping ' + mout + '\n' + '*'*40)

        if len(importexclude) == 0:
            exit(0)

        Classes.updateMapping(c=importinclude, exclude=importexclude)
        glb = Classes.mapping
