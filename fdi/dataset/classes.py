
# -*- coding: utf-8 -*-
import logging
import copy
import importlib
import traceback

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
        'fdi.dataset.datatypes': ['Vector', 'Quaternion'],
        'fdi.dataset.metadata': ['Parameter', 'NumericParameter', 'MetaData'],
        'fdi.dataset.dataset': ['GenericDataset', 'ArrayDataset',
                                'TableDataset', 'CompositeDataset', 'Column'],
        'fdi.pal.context': ['Context', 'MapContext', 'RefContainer',
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

    def updateMapping(cls, c=None, rerun=False, exclude=[]):
        """ Updates classes mapping.


        Set rerun=True to reimport module-class list and update mapping with it, with specified modules excluded, before updating with c. If the module-class list has never been imported, it will be imported regardless rerun.
        """
        #
        cls.importModuleClasses(rerun=rerun, exclude=exclude)
        # cls._classes.clear()
        cls._classes.update(copy.copy(cls._package))
        if c:
            cls._classes.update(c)

    def importModuleClasses(cls, rerun=False, exclude=[]):
        """ The set of eserializable classes in modclass is maintained by hand.
        Do nothing if the classes mapping is already made so repeated calls will not cost lots more time. Set rerun to True to force re-import. If the module-class list has never been imported, it will be imported regardless rerun.
modules whose names (without '.') are in exclude are not imported.
        """

        if len(cls._package) and not rerun:
            return
        cls._package.clear()
        SelectiveMetaFinder.exclude = exclude

        # print('With %s excluded..' % (str(exclude)))
        for modnm, froml in cls.modclass.items():
            if any((x in exclude for x in modnm.split('.'))):
                continue
            #print('importing %s from %s' % (str(froml), modnm))
            try:
                #m = importlib.__import__(modnm, globals(), locals(), froml)
                m = importlib.import_module(modnm)
            except SelectiveMetaFinder.ExcludedModule as e:
                logger.error('Importing %s not successful. %s' %
                             (str(froml), str(e)))
                #ety, enm, tb = sys.exc_info()
            else:
                for n in froml:
                    #print(n, m)
                    # print(dir(m))
                    cls._package[n] = getattr(m, n)

        return

    def reloadClasses(cls):
        """ re-import classes in mapping list, which is supposed to be populated. """
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

        return cls._classes

    @mapping.setter
    def mapping(cls, c):
        """ Delegated to cls.update...().
        """
        raise NotImplementedError('Use Classes.updateMapping(c).')
        cls.updateMapping(c)

    def get(cls, name):
        """ returns class objects by name """
        if len(cls._classes) == 0:
            cls.updateMapping()
        return cls._classes[name]


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


globals()
# pdb.set_trace()
# Classes.importModuleClasses()
