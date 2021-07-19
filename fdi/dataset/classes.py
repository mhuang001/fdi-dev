# -*- coding: utf-8 -*-

from ..utils.common import trbk
from ..utils.moduleloader import SelectiveMetaFinder, installSelectiveMetaFinder

import sys
import logging
import copy
import importlib

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


class Classes_meta(type):
    """ metaclass for 'classproperty'.
        # https://stackoverflow.com/a/1800999
    """
    # modules and classes to import from them
    module_class = {
        'fdi.dataset.deserialize': ['deserialize'],
        'fdi.dataset.listener': ['ListnerSet'],
        'fdi.dataset.serializable': ['Serializable'],
        'fdi.dataset.eq': ['DeepEqual'],
        'fdi.dataset.odict': ['ODict'],
        'fdi.dataset.finetime': ['FineTime', 'FineTime1', 'utcobj'],
        'fdi.dataset.history': ['History'],
        'fdi.dataset.baseproduct': ['BaseProduct'],
        'fdi.dataset.product': ['Product'],
        'fdi.dataset.testproducts': ['TP', 'TC', 'TM'],
        'fdi.dataset.datatypes': ['Vector', 'Vector2D', 'Quaternion'],
        'fdi.dataset.metadata': ['AbstractParameter', 'Parameter', 'MetaData'],
        'fdi.dataset.numericparameter': ['NumericParameter'],
        'fdi.dataset.dateparameter': ['DateParameter'],
        'fdi.dataset.stringparameter': ['StringParameter'],
        'fdi.dataset.arraydataset': ['ArrayDataset', 'Column'],
        'fdi.dataset.dataset': ['GenericDataset', 'CompositeDataset'],
        'fdi.dataset.tabledataset': ['TableDataset', 'IndexedTableDataset'],
        'fdi.dataset.readonlydict': ['ReadOnlyDict'],
        'fdi.pal.context': ['AbstractContext', 'Context',
                            'AbstractMapContext', 'MapContext',
                            'RefContainer',
                            'ContextRuleException'],
        'fdi.pal.urn': ['Urn'],
        'fdi.pal.productref': ['ProductRef'],
        'fdi.pal.query':  ['AbstractQuery', 'MetaQuery', 'StorageQuery'],
    }

    # class list from the package
    _package = {}
    # class list with modifcation
    _classes = {}

    def __init__(cls, *args, **kwds):
        """ Class is initialized with built-in classes by default.
        """
        super().__init__(*args, **kwds)

    def updateMapping(cls, c=None, rerun=False, exclude=None, ignore_missing=False, verbose=False, ignore_error=False):
        """ Updates classes mapping.
        Make the package mapping if it has not been made.
        """
        if exclude is None:
            exclude = []
        try:
            cls.importModuleClasses(rerun=rerun, exclude=exclude,
                                    ignore_error=ignore_error,  verbose=verbose)
        except (ModuleNotFoundError, SyntaxError) as e:
            if ignore_error:
                logger.warning('!'*80 +
                               '\nUnable to import "%s" module. Ignored\n' % clp +
                               '!'*80+'\n'+str(e)+'\n'+'!'*80)
            else:
                raise

        # cls._classes.clear()
        cls._classes.update(copy.copy(cls._package))
        if c:
            cls._classes.update(c)
        return cls._classes

    def importModuleClasses(cls, rerun=False, exclude=None, ignore_error=False, verbose=False):
        """ The set of deserializable classes in module_class is maintained by hand.

        Do nothing if the classes mapping is already made so repeated calls will not cost  more time.

        rerun: set to True to force re-import. If the module-class list has never been imported, it will be imported regardless rerun.
        exclude: modules whose names (without '.') are in exclude are not imported.
        """

        if len(cls._package) and not rerun:
            return
        if exclude is None:
            exclude = []

        cls._package.clear()
        SelectiveMetaFinder.exclude = exclude
        msg = 'With %s excluded.. and SelectiveMetaFinder.exclude=%s' % (
            str(exclude), str(SelectiveMetaFinder.exclude))
        if verbose:
            logger.info(msg)
        else:
            logger.debug(msg)

        for module_name, class_list in cls.module_class.items():
            exed = [x for x in class_list if x not in exclude]
            if len(exed) == 0:
                continue
            msg = 'importing %s from %s' % (str(class_list), module_name)
            if verbose:
                logger.info(msg)
            else:
                logger.debug(msg)
            try:
                #m = importlib.__import__(module_name, globals(), locals(), class_list)
                m = importlib.import_module(module_name)
            except SelectiveMetaFinder.ExcludedModule as e:
                msg = 'Did not import %s. %s' % (str(class_list), str(e))
                if verbose:
                    logger.info(msg)
                else:
                    logger.debug(msg)
                #ety, enm, tb = sys.exc_info()
            except SyntaxError as e:
                msg = 'Could not import %s. %s' % (str(class_list), str(e))
                logger.error(msg)
                raise
            except ModuleNotFoundError as e:
                msg = 'Could not import %s. %s' % (str(class_list), str(e))
                if ignore_error:
                    if verbose:
                        logger.info(msg)
                    else:
                        logger.debug(msg)
                else:
                    logger.error(msg)
                    raise
            else:
                for n in exed:
                    cls._package[n] = getattr(m, n)

        return

    def reloadClasses(cls):
        """ re-import classes in list. """
        for n, t in cls._classes.items():
            mo = importlib.import_module(t.__module__)
            importlib.reload(mo)
            m = importlib.__import__(t.__module__, globals(), locals(), [n])
            cls._classes[n] = getattr(m, n)

    # https://stackoverflow.com/a/1800999
    @property
    def mapping(cls):
        """ Returns the dictionary of classes allowed for deserialization, including the fdi built-ins and user added classes.

        Will update the classes if the list is empty
        """
        if len(cls._classes) == 0:
            cls.updateMapping()
        return cls._classes

    @mapping.setter
    def mapping(cls, c):
        """ Delegated to cls.update...().
        """
        raise NotImplementedError('Use Classes.updateMapping(c).')
        cls.updateMapping(c)


class Classes(metaclass=Classes_meta):
    """ A dictionary of class names and their class objects that are allowed to be deserialized.
    A fdi package built-in dictionary (in the format of locals() output) is kept internally.
    Users who need add more deserializable class can for example:


    Define new classes
    ``class Myclass():
          ....``    

    update Classes
    ``Classes.classes.update({'myClasses': MyClass})``

    and use
    ``new_instance = Classes.mapping['MyClass']``

    For a new package with many classes: 

    Import user classes in a python file for example projectclasses.py:

    ``
    Class PC(Classes):

        module_class = {
            'mypackage.mymodule': ['MyClass1', 'MyClass2'],
        }
        # from another module defining a dict of modulename-Classobj pairs
        try:
            from mypackage.mymodule import pairs
        except (ImportError, ModuleNotFoundError) as e:
            logger.info(e)
        else:
            module_class.update(pairs)

        _package = {}
        _classes = {}
    ``

    To use:
    ``
    from fdi.dataset.classes import Classes
    from my.package.projectclasses import PC
    prjcls = Classes.mapping
    Classes.updateMapping(PC.updateMapping())

    new_instance = prjcls['MyClass1']

    """

    pass


# globals()
# Classes.importModuleClasses()
