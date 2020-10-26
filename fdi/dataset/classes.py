# -*- coding: utf-8 -*-
import logging
import copy
import importlib

import pdb

from .odict import ODict
from ..utils.common import trbk
from ..utils.moduleloader import SelectiveMetaFinder, installSelectiveMetaFinder
import sys
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
    modclass = {
        'fdi.dataset.deserialize': ['deserializeClassID'],
        'fdi.dataset.listener': ['ListnerSet'],
        'fdi.dataset.serializable': ['Serializable'],
        'fdi.dataset.eq': ['DeepEqual'],
        'fdi.dataset.odict': ['ODict'],
        'fdi.dataset.finetime': ['FineTime', 'FineTime1', 'utcobj'],
        'fdi.dataset.history': ['History'],
        'fdi.dataset.baseproduct': ['BaseProduct'],
        'fdi.dataset.product': ['Product'],
        'fdi.dataset.testproducts': ['TP', 'TC', 'TM'],
        'fdi.dataset.datatypes': ['Vector', 'Quaternion'],
        'fdi.dataset.metadata': ['AbstractParameter', 'Parameter', 'NumericParameter', 'DateParameter', 'StringParameter', 'MetaData'],
        'fdi.dataset.dataset': ['GenericDataset', 'ArrayDataset',
                                'TableDataset', 'CompositeDataset', 'Column'],
        'fdi.pal.context': ['AbstractContext', 'Context',
                            'AbstractMapContext', 'MapContext',
                            'RefContainer',
                            'ContextRuleException'],
        'fdi.pal.urn': ['Urn'],
        'fdi.pal.productref': ['ProductRef']
    }

    # class list from the package
    _package = {}
    # class list with modifcation
    _classes = {}

    def __init__(cls, *args, **kwds):
        """ Class is initialized with built-in classes by default.
        """
        super().__init__(*args, **kwds)

    def updateMapping(cls, c=None, rerun=False, exclude=[], verbose=False):
        """ Updates classes mapping.
        Make the package mapping if it has not been made.
        """
        #
        cls.importModuleClasses(rerun=rerun, exclude=exclude, verbose=verbose)
        # cls._classes.clear()
        cls._classes.update(copy.copy(cls._package))
        if c:
            cls._classes.update(c)
        return cls._classes

    def importModuleClasses(cls, rerun=False, exclude=[], verbose=False):
        """ The set of eserializable classes in modclass is maintained by hand.
        Do nothing if the classes mapping is already made so repeated calls will not cost lots more time. Set rerun to True to force re-import. If the module-class list has never been imported, it will be imported regardless rerun.
modules whose names (without '.') are in exclude are not imported.
        """

        if len(cls._package) and not rerun:
            return
        cls._package.clear()
        SelectiveMetaFinder.exclude = exclude

        if verbose:
            logger.info('With %s excluded..' % (str(exclude)))
        else:
            logger.debug('With %s excluded..' % (str(exclude)))

        for modnm, froml in cls.modclass.items():
            exed = [x for x in froml if x not in exclude]
            if len(exed) == 0:
                continue
            if verbose:
                logger.info('importing %s from %s' % (str(froml), modnm))
            else:
                logger.debug('importing %s from %s' % (str(froml), modnm))
            try:
                #m = importlib.__import__(modnm, globals(), locals(), froml)
                m = importlib.import_module(modnm)
            except SelectiveMetaFinder.ExcludedModule as e:
                if verbose:
                    logger.info('Did not import %s. %s' %
                                (str(froml), str(e)))
                else:
                    logger.debug('Did not import %s. %s' %
                                 (str(froml), str(e)))
                #ety, enm, tb = sys.exc_info()
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
    def myclasses():
        from foo.bar import Baz
        ...
    Classes.classes = myClasses
    """

    pass


# globals()
# pdb.set_trace()
# Classes.importModuleClasses()
