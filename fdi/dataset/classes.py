# -*- coding: utf-8 -*-

from ..utils.common import trbk
from ..utils.moduleloader import SelectiveMetaFinder, installSelectiveMetaFinder
from .namespace import Load_Failed, NameSpace_meta
from collections import ChainMap
import sys
import logging
import copy
import importlib
from functools import lru_cache

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


''' Note: this has to be in a different file where other interface
classes are defined to avoid circular dependency (such as ,
Serializable.
'''

# modules and classes to import from them

Modules_Classes = {
    'fdi.dataset.deserialize': ['deserialize'],
    'fdi.dataset.listener': ['ListenerSet'],
    'fdi.dataset.serializable': ['Serializable'],
    'fdi.dataset.eq': ['DeepEqual'],
    'fdi.dataset.odict': ['ODict'],
    'fdi.dataset.finetime': ['FineTime', 'FineTime1', 'utcobj'],
    'fdi.dataset.history': ['History'],
    'fdi.dataset.baseproduct': ['BaseProduct'],
    'fdi.dataset.product': ['Product'],
    'fdi.dataset.browseproduct': ['BrowseProduct'],
    'fdi.dataset.testproducts': ['TP', 'TC', 'TM'],
    'fdi.dataset.datatypes': ['Vector', 'Vector2D', 'Vector3D', 'Quaternion'],
    'fdi.dataset.metadata': ['AbstractParameter', 'Parameter', 'MetaData'],
    'fdi.dataset.numericparameter': ['NumericParameter', 'BooleanParameter'],
    'fdi.dataset.dateparameter': ['DateParameter'],
    'fdi.dataset.stringparameter': ['StringParameter'],
    'fdi.dataset.arraydataset': ['ArrayDataset', 'Column'],
    'fdi.dataset.mediawrapper': ['MediaWrapper'],
    'fdi.dataset.dataset': ['GenericDataset', 'CompositeDataset'],
    'fdi.dataset.tabledataset': ['TableDataset', 'IndexedTableDataset'],
    'fdi.dataset.unstructureddataset': ['UnstructuredDataset'],
    'fdi.dataset.readonlydict': ['ReadOnlyDict'],
    'fdi.pal.context': ['AbstractContext', 'Context',
                        'MapContext',
                        'RefContainer',
                        'ContextRuleException'],
    'fdi.pal.urn': ['Urn'],
    'fdi.pal.productref': ['ProductRef'],
    'fdi.pal.query':  ['AbstractQuery', 'MetaQuery', 'StorageQuery'],
    # 'fdi.utils.common': ['UserOrGroupNotFoundError'],
}

Class_Module_Map = dict((c, m)
                        for m, clses in Modules_Classes.items() for c in clses)


def load(key, mapping, remove=True,
         exclude=None, ignore_error=False,
         verbose=False):

    res = importModuleClasses(key, mapping=mapping,
                              exclude=exclude,
                              ignore_error=ignore_error,
                              verbose=verbose
                              )
    return res


class Classes(metaclass=NameSpace_meta,
              default_map=Class_Module_Map,
              extension_maps=None,
              load=load
              ):
    """ A dictionary of class names and their class objects that are allowed to be deserialized.

    An fdi package built-in dictionary is loaded from the module `Class_Module_Map`. Users who need add more deserializable class can for example:

    """


logger.info(str(Class_Module_Map))


def importModuleClasses(scope=None, mapping=None,
                        exclude=None, ignore_error=False,
                        verbose=False):
    """ The set of deserializable classes in default_map is
    maintained by hand.

    Do nothing if the classes mapping is already made so repeated
    calls will not cost  more time.

    Parameters
    ----------

    scope : NoneType, string, list
       If is None, import all classes in `default_map`; if is a
    mapping: mapping
        A mapping to get module names with class names. If returns a class object for a key, the object will be the value in the returned dict for the key.
    string, take it as a fully qualified module name and only load
    its member classes; if is a list, take it as a list of module names.
    exclude : list
        Modules whose names (without '.') are in exclude are not imported. Default is empty.
    ignore_error : boolean
        IF set class importing errors will be logged but otherwise ignored. Default is `False`.

    Returns
    -------
    dict:
       Key and load-result pairs. load-result is `.namespace.Load_Failed` if loading of the key was not successful.
    """

    if exclude is None:
        exclude = []

    if scope is None:
        return {}
    elif issubclass(scope.__class__, str):
        scope = [scope]
    if mapping is None:
        mapping = Class_Module_Map

    SelectiveMetaFinder.exclude = exclude
    msg = 'With %s excluded.. and SelectiveMetaFinder.exclude=%s' % (
        str(exclude), str(SelectiveMetaFinder.exclude))
    if verbose:
        logger.info(msg)
    else:
        logger.debug(msg)

    res = {}
    for cl in scope:
        module_name = mapping[cl]
        if isinstance(module_name, type):
            res[cl] = module_name
            continue
        # if we cannot find the module we make a class list
        class_list = Modules_Classes.get(module_name, [cl])
        left = [x for x in class_list if x not in exclude]
        if len(left) == 0:
            continue
        msg = 'importing %s from %s...' % (str(class_list), module_name)

        try:
            #m = importlib.__import__(module_name, globals(), locals(), class_list)
            m = importlib.import_module(module_name)
        except SelectiveMetaFinder.ExcludedModule as e:
            msg += ' Did not import %s, as %s' % (str(class_list), str(e))
            #ety, enm, tb = sys.exc_info()
        except SyntaxError as e:
            msg += ' Could not import %s, as %s' % (
                str(class_list), str(e))
            logger.error(msg)
            raise
        except ModuleNotFoundError as e:
            msg += ' Could not import %s, as %s' % (
                str(class_list), str(e))
            if ignore_error:
                msg += ' Ignored.'
            else:
                logger.error(msg)
                raise
        else:
            for n in left:
                res[n] = getattr(m, n)

        if verbose:
            logger.info(msg)
        else:
            logger.debug(msg)

    return res
