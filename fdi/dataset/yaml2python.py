#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from ..pal.context import MapContext
from ..utils.common import lls, trbk, find_all_files
from ..utils.ydump import yinit, ydump
from ..utils.moduleloader import SelectiveMetaFinder, installSelectiveMetaFinder
from .attributable import make_class_properties
# a dictionary that translates metadata 'type' field to classname
from .datatypes import DataTypes, DataTypeNames

# from ruamel.yaml import YAML
# import yaml
from collections import OrderedDict
import os
import sys
import functools
from itertools import chain
from string import Template
from datetime import datetime
import importlib
import argparse

import logging

# create logger
logger = logging.getLogger()
logging.basicConfig(stream=sys.stdout,
                    format='%(asctime)s -%(levelname)4s'
                           ' -[%(filename)s:%(lineno)3s'
                           ' -%(funcName)10s()] - %(message)s',
                    datefmt="%Y%m%d %H:%M:%S")
logging.getLogger().setLevel(logging.DEBUG)

global version

version = '1.8'
""" schema version. The attribute `FORMATV` will have this schema version, hand-set version, and revision

1.10: 'Instrument', 'VT', 'VT_PDPU' moved to svom.products.vt, 'GRM' are in svom.products.grm.'; FORMATV becomes $(schema_v}.${revision}
1.9: remove version.
1.8: 'Instrument', 'VT', 'VT_PDPU', 'GFT', 'GRM' are in svom.instrument'
1.6  FORMATV becomes $(schema_v}.${version_v}; dummy dataset.
"""
global revision

revision = ''


# make simple demo for fdi
demo = 0
# if demo is true, only output this subset.
onlyInclude = ['default', 'description',
               'data_type', 'unit', 'valid', 'fits_keyword']
# inlcude allVersions]
onlyInclude = None

# only these attributes in meta
attrs = ['startDate', 'endDate', 'instrument', 'modelName', 'mission', 'type']
indent = '    '
# extra indent
ei = ''
indents = [ei + indent * i for i in range(10)]

fmtstr = {
    'boolean': '{!r}',
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
    Parameters
    ---------

    Returns
    -------
    """

    if "'" in s or '\n' in s:
        qm = '""' if '"' in s or '\n' in s else '"'
    else:
        qm = "'"
    return '%s%s%s' % (qm, s, qm)


def get_Python(val, indents, demo, onlyInclude, debug=False):
    """ make Model and init__() code strings from given data.

    Parameters
    ----------
    val : dict
       starting from the top it is the whole document then is meta then...
    Returns
    -------
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
                #   description: Description of this parent_dataset
                #   default: UNKNOWN
                #   valid: ''
                # v is a dict of parameter attributes
                istr, d_code = params(
                    v, indents[1:], demo, onlyInclude, debug=debug)
            else:
                # headers such as name, parents, schema metadata...
                # extra care to these:
                if k == 'FORMATV':
                    v += f'.{revision}' if v else revision
                istr, d_code = get_Python(
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
                    v, indents[1:], demo, onlyInclude, prev_level=val, debug=debug)
            else:
                istr, d_code = get_Python(
                    v, indents[1:], demo, onlyInclude, debug=debug)
            infostr += istr
            code.append(d_code)
        infostr += indents[0] + '],\n'
    else:
        # constants
        pval = sq(val) if issubclass(val.__class__, (str, bytes)) else str(val)
        infostr += pval + ',\n'
        code = pval

    return infostr, code


def make_init_code(dt, pval):
    """ python instanciation source code.

    will be like "default: FineTime1(0)" in 'def __init__(self...'
    Parameters
    ----------

    Returns
    -------
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
    """ generates python string for val, a parameter with a set of attributes

    val: as in ```name:val```
    ```
    nam:
        data_type: string
        description: Description of this parent_dataset
        default: UNKNOWN
        valid: ''
    ```
    see get_Python
    Parameters
    ----------

    Returns
    -------
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
        if demo and (onlyInclude is not None) and pname not in onlyInclude:
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
                code = make_init_code(dt, pval)
            if pname in ['example', 'default']:
                # here data_type instead of input type determines the output type
                iss = (val['data_type'] == 'string') and (pval != 'None')
            s = sq(pval) if iss else pval
        modelString += indents[1] + '%s: %s,\n' % (sq(pname), s)
    modelString += indents[1] + '},\n'

    return modelString, code


def get_projectclasses(clp, exclude=None, verbose=False):
    """
    return a `Classes` object that is going  to give {class-name:class-type} from a file at gieven location.

    Parameters
    ----------
    :clp: path of the mapping file.
    :rerun, exclude: from `Classes`

    Returns
    -------
    The `classes.Classes` object.
    """

    if clp is None or len(clp.strip()) == 0:
        return None

    if exclude is None:
        exclude = []
    if '/' not in clp and '\\' not in clp and not clp.endswith('.py'):
        print('Importing project classes from module '+clp)
        # classes path not given on command line
        pc = importlib.import_module(clp)
        print(
            'Imported project classes from %s module.' % clp)

    else:
        clpp, clpf = os.path.split(clp)
        sys.path.insert(0, os.path.abspath(clpp))
        # print(sys.path)
        print('Importing project classes from file '+clp)
        pc = importlib.import_module(clpf.replace('.py', ''))
        sys.path.pop(0)
    return pc


def read_yaml(ypath, version=None, verbose=False):
    """ read YAML files in ypath.

    Parameters
    ----------

    Returns
    -------
    tuple
        (nm, desc)
        nm is  stem of file name. desc is descriptor, key being yaml[name]

    """
    yaml = yinit()
    desc = OrderedDict()
    fins = {}
    if isinstance(ypath, str):
        ypathl = [ypath]
    else:
        ypathl = ypath

    # ypathla = map(os.path.abspath, ypathl)
    all_f = [find_all_files(y, include='*.y*ml', absdir=True) for y in ypathl]
    for file_in_dir in chain(*all_f):
        ''' The  input file name ends with '.yaml' or '.yml' (case insensitive).
        the stem name of output file is input file name stripped of the extension.
        '''
        dir_only, file_name = tuple(file_in_dir.rsplit('/', 1))
        # make it all lower case
        finl = file_name.lower()
        stem = os.path.splitext(file_name)[0]
        fins[stem] = (dir_only, finl)

        # read YAML
        print('--- Reading ' + file_in_dir + '---')
        with open(file_in_dir, 'r', encoding='utf-8') as f:

            # pyYAML d = OrderedDict(yaml.load(f, Loader=yaml.FullLoader))
            ytext = f.read()
        y = yaml.load(ytext)
        d = dict(OrderedDict(y))

        if 'schema' in d and float(d['schema']) < 1.2:
            raise NotImplemented('Schema %s is too old.' % d['schema'])
        if 'metadata' not in d or d['metadata'] is None:
            d['metadata'] = {}
        if 'datasets' not in d or d['datasets'] is None:
            d['datasets'] = {}

        attrs = dict(d['metadata'])
        datasets = dict(d['datasets'])
        # move primary level table to datasets, named 'TABLE_META'
        if 'TABLE' in attrs:
            datasets['TABLE_META'] = {}
            datasets['TABLE_META']['TABLE'] = attrs['TABLE']
            del attrs['TABLE']
        if verbose:
            print('Pre-emble:\n%s' %
                  (''.join([k + '=' + str(v) + '\n'
                            for k, v in d.items() if k not in ['metadata', 'datasets']])))

        logger.debug('Find attributes:\n%s' %
                     ''.join(('%20s' % (k+'=' + str(v['default'])
                                        if 'default' in v else 'url' + ', ')
                              for k, v in attrs.items()
                              )))
        itr = ('%20s' % (k+'=' + str([c for c in (v['TABLE'] if 'TABLE'
                                                  in v else [])]))
               for k, v in datasets.items())
        logger.debug('Find datasets:\n%s' % ', '.join(itr))

        desc[d['name']] = (d, attrs, datasets, fins)
    return desc


def output(nm, d, yaml_dir, version, dry_run=False, verbose=False):
    """
    Parameters
    ----------
    nm : str
        Model nameand also yaml file name stem.
    yaml_dir : str
          yaml file direcrory.
    Returns
    -------
    """
    filen = nm + '.yml'
    print("Input YAML file is to be renamed to " + filen + '.old')
    fout = os.path.join(yaml_dir, filen)
    print("Output YAML file is "+fout)
    if dry_run:
        print('Dry run.')
        ydump(d, sys.stdout)  # yamlfile)
    else:
        os.rename(fout, fout+'.old')
        with open(fout, 'w', encoding='utf-8') as yamlfile:
            ydump(d,  yamlfile)


def yaml_upgrade(descriptors, ypath, version, dry_run=False, verbose=False):
    """
    Parameters
    ----------
    descriptors : list
        A list of tuples of nested dicts describing the data model. and filename info.
    version : str
          current version. not that in the yaml to be modified.

    Returns
    -------
    """
    # global version
    global revision

    target_version = float(version)

    for nm, daf in descriptors.items():
        d, attrs, datasets, fins = daf
        in_doc_schema = float(d['schema'])
        # __import__("pdb").set_trace()

        if target_version == 1.9:
            # this one is from the future
            if in_doc_schema >= target_version:
                print(
                    f'No need to upgrade {nm}.yml of {in_doc_schema} to {target_version}.')
                continue
            elif in_doc_schema < 1.6:
                logger.error(nm + ' version not good: '+d['schema'])
                exit(1)

            # make FORMATV
            w = d['metadata']['FORMATV'].strip()
            sch_ = d['schema']
            if w.startswith(sch):
                # remove schema and a '.'
                in_doc_v_ = w[len(sch)+1:]
            else:
                in_doc_v_ = w
            # set command version
            d['schema'] = version
            # w.clear()
            # add revision
            w['default'] = f'{version}.{revision}'
            if 0:
                output(nm, d, fins[nm][0], version,
                       dry_run=dry_run, verbose=verbose)
        elif target_version == 1.8:
            # this one is from the future
            if in_doc_schema >= target_version:
                print(
                    f'No need to upgrade {nm}.yml of {in_doc_schema} to {target_version}.')
                continue
            elif in_doc_schema < 1.6:
                logger.error(nm + ' version not good: '+d['schema'])
                exit(2)

            logger.info(nm + ' apply changes of ' + version)
            d['schema'] = version
            newp = []
            for p in d['parents']:
                if p in ['Instrument', 'VT', 'VT_PDPU', 'GFT', 'GRM']:
                    newp.append('svom.instruments.' + p)
                else:
                    newp.append(p)
            d['parents'] = newp
            # increment FORMATV
            w = d['metadata']['FORMATV']
            v = w['default'].split('.')
            # w.clear()
            w['default'] = version + '.' + \
                v[2] + '.' + str(int(v[3])+1)
            # v1.8
            if 0:
                output(nm, d, fins[nm][0], version,
                       dry_run=dry_run, verbose=verbose)
        elif target_version == 1.6:
            if in_doc_schema >= target_version:
                print(f'No need to upgrade {nm}.yml of {in_doc_schema}.')
                continue
            elif in_doc_schema < 1.6:
                logger.error(nm + ' version not good: '+d['schema'])
                exit(1)
            logger.info('apply changes of ' + version)
            d['schema'] = version
            level = d.pop('level')
            md = OrderedDict()
            for pname, w in d['metadata'].items():
                # dt = w['data_type']
                # no parent_dataset yet
                if pname == 'type':
                    v = w['default']
                    w.clear()
                    w['default'] = v
                    md[pname] = w
                    md['level'] = {'default': 'C' + level.upper()}
                elif pname == 'FORMATV':
                    v = w['default'].split('.')
                    # w.clear()
                    w['default'] = version + '.' + \
                        v[2] + '.' + str(int(v[3])+1)
                    md[pname] = w
                else:
                    md[pname] = w
            d['metadata'] = md
            if 'datasets' not in d:
                d['datasets'] = {}
            # v1.6
            if 0:
                output(nm, d, fins[nm][0], version,
                       dry_run=dry_run, verbose=verbose)
        else:
            logger.error('Given version not good: '+version)
            exit(-1)
        return d


verbo = 9


@functools.lru_cache
def mro_cmp(cn1, cn2):
    """ compare two classes by their MRO relative positions.

    Parameters
    ----------
    cn1 : str
        classname
    cn2 : str
        classname

    Returns
    -------
    int
        Returns -1 if class by the name of cn2 is a parent that of cn1,
    0 if c1 and c2 are the same class; 1 for c1 being superclasses or no relation.
    """

    if not (cn1 and cn2 and issubclass(cn1.__class__, str) and issubclass(cn2.__class__, str)):
        raise TypeError('%s and %s must be classnames.' % (str(cn1), str(cn2)))
    if verbo:
        print('...mro_cmp ', cn1, cn2)
    if cn1 == cn2:
        # quick result
        return 0
    try:
        c1 = glb[cn1]
    except TypeError as e:
        logger.error(f'{trbk(e)}: {cn1}: {e}')
        exit(-6)
    try:
        c2 = glb[cn2]
    except TypeError as e:
        logger.error(f'{trbk(e)}: {cn2}: {e}')
        exit(-6)

    if c1 is None or c2 is None:
        return None
    res = 0 if (c1 is c2) else -1 if issubclass(c1, c2) else 1
    if verbo:
        print('... ', c1, c2, res)
    return res


def descriptor_mro_cmp(nc1, nc2, des):
    """ find if nc1 is a subclasss of nc1.

    cn1 : str
        classname
    cn2 : str
        classname
    Returns
    -------
    int
        Returns -1 if class by the name of cn2 is a parent that of cn1 or its parent,
    0 if c1 and c2 are the same class; 1 for c1 being superclasses or no relation. This is to be used by `cmp_to_key` so besides having to return a negative number if `mro(nc1)` < `mro(nc2)`, it cannot return `None` for invalid situations.
  """

    if verbo:
        print('*** des_m_cmp', nc1, nc2)

    mc = mro_cmp(nc1, nc2)
    if verbo:
        print('**** mro_cmp', mc)

    if mc is None:
        if nc1 not in des:
            return 0
        # no class definition
        # 0 for top level
        parents = des[nc1][0]['parents']
        if len(parents) == 0 or len(parents) == 1 and parents[0] is None:
            return 0
        if nc1 in parents:
            raise ValueError(
                nc1 + ' cannot be its own parent. Check the YAML file.')
        if verbo:
            print(f"***** parents for {nc1} found: {parents}")
        for p in parents:
            if p == nc2:
                # This is where parent-in-des case answered.
                # parent is subclass so nc1 must be nc2's subclass
                if verbo:
                    print(f'{nc1} parent is {nc2}.')
                return -1
            else:
                dmc = descriptor_mro_cmp(p, nc2, des)
            if dmc == -1:
                # parent is subclass so nc1 must be nc2's subclass
                if verbo:
                    print(f'{nc1} parent is subc of {nc2}. d{dmc}')
                return -1
        else:
            if verbo:
                print(f'{nc1} parent is not subc of {nc2}. d{dmc}')
            return 0
    else:
        # nc1 is subclass or the same class.
        if verbo:
            print(f'{nc1} vs {nc2} => {mc}')

        return mc


def dependency_sort(descriptors):
    """ sort the descriptors so that everyone's parents are to his right.
    Parameters
    ----------

    Returns
    -------
    """
    ret = []
    # make a list of prodcts
    working_list = list(descriptors.keys())
    if verbo:
        print('+++++', str('\n'.join(working_list)))

    working_list.sort(key=functools.cmp_to_key(
        functools.partial(descriptor_mro_cmp, des=descriptors)))

    if verbo:
        print('!!!!!', str('\n'.join(working_list)))
    return working_list

    while len(working_list):
        # examin one by one
        # must use index to loop
        for i in range(len(working_list)):
            # find parents of i
            nm = working_list[i]
            # 0 for top level
            p = descriptors[nm][0]['parents']
            if nm in p:
                raise ValueError(nm + 'cannot be its own parent.')
            nm_found_parent = False
            if len(p) == 0:
                continue
            found = set(working_list) & set(p)
            # type_of_nm = glb[nm]
            # found2 = any(issubclass(type_of_nm, glb[x])
            #              for x in working_list if x != nm)
            # assert bool(len(found)) == found2
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
        if verbo:
            print(i, nm, p, working_list)

    return ret


def remove_Parent(a, b):
    """ Returns the one who is the other one's parent.
    Parameters
    ----------
    :a: a class name
    :b: a class name

    Returns
    -------
    classname if found or `None`.
    """
    if a == b:
        logger.debug('%s and %s are the same class' % (b, a))
        return None
    tmp = "remove parent %s because it is another parent %s's"
    ca, cb = glb[a], glb[b]
    if ca is None or cb is None:
        return None
    if issubclass(ca, cb):
        # remove b
        logger.debug(tmp % (b, a))
        return b
    elif issubclass(cb, ca):
        # remove a
        logger.debug(tmp % (a, b))
        return a
    else:
        return None
    # except TypeError as e:
    #    msg = f'Error finding class definition for {a} (found {glb[a]} and {b} (found {glb[b]}). Are they registered in projectclasses.py?'
     #   logger.error(msg)
    #     raise TypeError(msg) from e


def no_Parents_Parents(pn):
    """
    return a subset of class names such that no member is any other's parent.

    Parameters
    ----------
    :pn: list of class names.

    Returns
    -------
    list of non-parents.
    """

    removed = []
    for i in range(len(pn)-1):
        if pn[i] in removed:
            continue
        for j in range(i+1, len(pn)):
            r = remove_Parent(pn[i], pn[j])
            if r:
                removed.append(r)
            if r == pn[i]:
                break
    for r in removed:
        # more than one r could be in removed.
        if r in pn:
            pn.remove(r)
    return pn


def inherit_from_parents(parentNames, attrs, datasets, schema, seen):
    """ inherit metadata and datasets from parents.

    :attrs: metadata descriptor of the child
    :datasets: datasets descriptor of the child
    :seen: a dict holding class names that the py file is going to import
 """
    if parentNames and len(parentNames):
        parentsAttributes = OrderedDict()
        from collections import defaultdict
        temp = {}  # defaultdict(dict)
        parentsTableColumns = OrderedDict()
        for parent in parentNames:
            if not parent:
                continue
            mod_name = glb[parent].__module__
            if mod_name != 'builtins':
                s = 'from %s import %s' % (mod_name, parent)
            if parent not in seen:
                seen[parent] = s

            # get parent attributes and tables
            mod = sys.modules[mod_name]
            if hasattr(mod, '_Model_Spec'):
                temp.update(
                    mod._Model_Spec['metadata'])

                parentsTableColumns.update(
                    mod._Model_Spec['datasets'])
        # merge to get all attributes including parents' and self's.
        toremove = []
        for nam, val in attrs.items():
            # if 'FORMATV' == nam:
            #    __import__("pdb").set_trace()

            if float(schema) > 1.5 and 'data_type' not in val \
               and nam in temp:
                # update parent's
                temp[nam].update(attrs[nam])
                toremove.append(nam)
            else:
                # override
                temp[nam] = attrs[nam]
            # move attrs items to the front
            parentsAttributes[nam] = temp[nam]
            del temp[nam]
        for nam in toremove:
            del attrs[nam]
        parentsAttributes.update(temp)
        # set some absolute ones
        if 'type' in parentsAttributes:
            parentsAttributes.move_to_end('type', last=False)
        # first
        if 'description' in parentsAttributes:
            parentsAttributes.move_to_end('description', last=False)
        if 'version' in parentsAttributes:
            parentsAttributes.move_to_end('version')
        # last
        if 'FORMATV' in parentsAttributes:
            parentsAttributes.move_to_end('FORMATV')

        # parents are updated but names and orders follow the child's
        for ds_name, child_dataset in datasets.items():
            # go through datasets  TODO: ArrayDataset
            if ds_name not in parentsTableColumns:
                # child has a name that the parent does not have
                parentsTableColumns[ds_name] = child_dataset
                continue
            p_dset = parentsTableColumns[ds_name]
            # go through the child's dataset
            for name, c_val in child_dataset.items():
                # child has a name that the parent does not have
                if name not in p_dset:
                    p_dset[name] = c_val
                    continue
                # p and c have dataset name in common
                if name != 'TABLE':
                    # parameter in meta
                    p_dset.update(c_val)
                    continue
                p_tab = p_dset['TABLE']
                _tab = {}
                # go through the child columns
                for colname, col in c_val.items():
                    # child has a name that the parent does not have
                    if colname not in p_tab:
                        _tab[colname] = col
                        continue
                    p_tab[colname].update(col)
                    _tab[colname] = p_tab[colname]
                p_dset['TABLE'] = _tab
    else:
        parentsAttributes = attrs
        parentsTableColumns = datasets

    return parentsAttributes, parentsTableColumns


if __name__ == '__main__':

    print('Generating Python code for product class definition..')

    # Get input file name etc. from command line. defaut 'Product.yml'
    cwd = os.path.abspath(os.getcwd())
    ypath = cwd
    tpath = ''
    opath = ''
    dry_run = False

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=''
    )
    parser.add_argument("-v", "--verbose",  type=int, nargs='?', const=1,
                        default=0, help="Set level of debugging info.")
    parser.add_argument("-y", "--yamldir", nargs='*', default=ypath,
                        help='Input YAML file directory.')
    parser.add_argument("-t", "--template", type=str, default=tpath,
                        help='Product class template file directory. Default is the YAML dir.')
    parser.add_argument("-o", "--outputdir", type=str, default=opath,
                        help="Output directory for python files. Default is the parent directory of the YAML dir.")
    parser.add_argument("-p", "--packagename", default="",
                        help="Name of the package which the generated modules belong to when imported during code generation. Default is guessing from output path.")
    parser.add_argument("-c", "--userclasses", default="",
                        help="Python file name, or a module name,  to import prjcls to update Classes with user-defined classes which YAML file refers to.")
    parser.add_argument("-r", "--revision",
                        help="A string that is a revision identification, for example a git hash to be appended to attribute FORMATV.")
    parser.add_argument("-u", "--upgrade", action='store_true', default=False,
                        help="Upgrade the file to current schema, by yaml_upgrade(), to version " + version)
    parser.add_argument("-n", "--dry_run",  action='store_true', default=False,
                        help="No writing. Dry run.")
    parser.add_argument("-d", "--debug",  action='store_true', default=False,
                        help="run in pdb. typec 'c' to continue.")

    args = parser.parse_args()
    print(f'command line: {args}')
    verbose = args.verbose
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    ypath = args.yamldir
    cmd_tpath = args.template
    cmd_opath = args.outputdir
    cmd_package_name = args.packagename
    project_class_path = args.userclasses
    upgrade = args.upgrade
    revision = args.revision
    dry_run = args.dry_run
    debug = args.debug

    # now can be used as parents
    from .classes import Classes

    # No bomb out if some target modules are missing.
    Classes.mapping.ignore_error = True

    # input file
    descriptors = read_yaml(ypath, version, verbose)
    if upgrade:
        descriptemptors = yaml_upgrade(descriptors, ypath, version,
                                       dry_run=dry_run, verbose=verbose)

    # Do not import modules that are to be generated. Thier source code
    # could be  invalid due to unseccessful previous runs
    importexclude = [x.lower() for x in descriptors.keys()]
    importinclude = {}

    # activate a module loader that refuses to load excluded
    installSelectiveMetaFinder()

    # include project classes for every product so that products made just

    pc = get_projectclasses(project_class_path,
                            exclude=importexclude, verbose=verbose)

    spupd = pc.Classes.mapping if pc else {}
    glb = Classes.update(
        c=spupd,
        exclude=importexclude,
        extension=True,
        verbose=verbose) if pc else Classes.mapping
    # make a list whose members do not depend on members behind (to the left)
    sorted_list = dependency_sort(descriptors)

    sorted_list.reverse()
    skipped = []
    for nm in sorted_list:
        d, attrs, datasets, fins = descriptors[nm]
        print('************** Processing ' + nm + '***********')

        modelName = d['name']
        # module/output file name is YAML input file "name" with lowercase
        modulename = nm.lower()

        # set paths according to each file's path
        ypath = fins[nm][0]
        tpath = ypath if cmd_tpath == '' else cmd_tpath
        opath = os.path.abspath(os.path.join(ypath, '..')
                                ) if cmd_opath == '' else cmd_opath
        if cmd_package_name == '':
            ao = os.path.abspath(opath)
            if not ao.startswith(cwd):
                logger.error(
                    'Cannot derive package name from output dir and cwd.')
                exit(-3)
            package_name = ao[len(cwd):].strip('/').replace('/', '.')
        else:
            package_name = cmd_package_name
        logger.info("Package name: " + package_name)

        # schema
        schema = d['schema']

        # the generated source code must import these
        seen = {}
        imports = 'from collections import OrderedDict\n'
        # import parent classes
        parentNames = d['parents']
        # remove classes that are other's parent class (MRO problem)
        try:
            if parentNames and len(parentNames):
                parentNames = no_Parents_Parents(parentNames)
        except KeyError as e:
            logger.warning('!!!!!!!!!!! Skipped %s due to %s.' %
                           (nm, type(e).__name__+str(e)))
            skipped.append(nm)
            continue

        parentsAttributes, parentsTableColumns = \
            inherit_from_parents(parentNames, attrs, datasets, schema, seen)

        # make output filename, lowercase modulename + .py
        fout = os.path.join(opath, modulename + '.py')
        print("Output python file is "+fout)

        # class doc
        doc = f"{modelName} class schema {schema} inheriting {d['parents']}.\n\nAutomatically generated from {fins[nm][1]} on {datetime.now()}.\n\nDescription:\n{d['description']}"

        # parameter classes used in init code may need to be imported, too
        col, v, colnm, ds, att_nm, val, a, maybe = tuple([None]*8)
        try:
            # for nm, val in chain(parentsAttributes.items(),
            #                      chain(((colnm, v) for v in col)
            #                            for colnm, ds in
            #                            parentsTableColumns.items()
            #                            for col in ds.get('TABLE', {}).values()
            #                            )
            #                      ):
            tab = []
            for colnm, ds in parentsTableColumns.items():
                for ncol, col in ds.get('TABLE', {}).items():
                    tab.append((ncol, col))
            for att_nm, val in chain(parentsAttributes.items(),
                                     tab):
                #            print(val)
                if 0:  # 'data_type' not in val:
                    __import__('pdb').set_trace()
                else:
                    t = val['data_type']
                    try:
                        a = DataTypes[t]
                    except KeyError as e:
                        maybe = DataTypeNames.get(t, '')
                        logger.error(
                            f'"{t}" is an invalid type for {att_nm}.'
                            f'{"Do you mean "+maybe+"?" if maybe else ""}')
                        exit(-5)
                    if a in glb:
                        # this attribute class has module
                        s = 'from %s import %s' % (glb[a].__module__, a)
                        if a not in seen:
                            seen[a] = s
        except (ValueError, TypeError) as e:
            __import__("pdb").set_trace()
            pass
        # make metadata and parent_dataset dicts
        d['metadata'] = parentsAttributes
        d['datasets'] = parentsTableColumns

        output(nm, d, ypath, version,
               dry_run=dry_run, verbose=verbose)
        continue
        infs, default_code = get_Python(d, indents[1:], demo, onlyInclude)
        # remove the ',' at the end.
        modelString = (ei + '_Model_Spec = ' + infs).strip()[: -1]

        # keyword argument for __init__
        ls = []
        for x in parentsAttributes:
            arg = 'typ_' if x == 'type' else x
            val = default_code['metadata'][x]
            ls.append(' '*17 + '%s = %s,' % (arg, val))
        ikwds = '\n'.join(ls)

        # make class properties
        properties = make_class_properties(attrs)

        # make substitution dictionary for Template
        subs = {}
        subs['WARNING'] = '# Automatically generated from %s. Do not edit.' % (
            os.path.join(fins[nm][0], nm+'.yml'))
        pass
        subs['MODELNAME'] = modelName
        print('product name: %s' % subs['MODELNAME'])
        subs['PARENTS'] = ', '.join(c for c in parentNames if c)
        print('parent class: %s' % subs['PARENTS'])
        subs['IMPORTS'] = imports + '\n'.join(seen.values())
        print('import class: %s' % ', '.join(seen.keys()))
        subs['CLASSDOC'] = doc
        subs['MODELSPEC'] = modelString
        subs['INITARGS'] = ikwds
        print('%s=\n%s\n' %
              ('Model Initialization', lls(subs['INITARGS'], 250)))
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
        if dry_run:
            print('Dry-run. Not saving ' + fout + '\n' + '='*40)
        else:
            with open(fout, 'w', encoding='utf-8') as f:
                f.write(sp)
            print('Done saving ' + fout + '\n' + '='*40)

        # import the newly made module to test and, for class generatiom, so the following classes could use it
        importexclude.remove(modulename)
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
        importlib.invalidate_caches()
        logger.debug('sys.path is '+str(sys.path))

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
            raise
        importexclude.extend(exclude_save)
        print('Imported ' + newp)
        # Instantiate and dump metadata in other formats

        prod = glb[modelName]()
        # [('fancy_grid', '.txt'), ('rst', '.rst')]:
        for fmt, ext in [('fancy_grid', '.txt')]:
            fg = {'name': 15, 'value': 18, 'unit': 7, 'type': 8,
                  'valid': 26, 'default': 18, 'code': 4, 'description': 30}
            sp = prod.meta.toString(tablefmt=fmt, param_widths=fg)

            mout = os.path.join(ypath, modelName + ext)
            if dry_run:
                print('Dry-run. Not dumping ' + mout + '\n' + '*'*40)
            else:
                with open(mout, 'w', encoding='utf-8') as f:
                    f.write(sp)
                print('Done dumping ' + mout + '\n' + '*'*40)

        if len(importexclude) == 0:
            exit(0)

        Classes.update(c=importinclude, exclude=importexclude)
        glb = Classes.mapping

    if len(skipped):
        print('!!!!!!!!!!! Skipped: %s possiblly due to unresolved dependencies. Try re-running.   !!!!!!!!!!!' % str(skipped))
