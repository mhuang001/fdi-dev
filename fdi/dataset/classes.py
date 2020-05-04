# -*- coding: utf-8 -*-
import logging
import copy

import pdb

from .odict import ODict
from ..utils.common import trbk

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

    _package = None
    _classes = None

    def __init__(cls, *args, **kwds):
        """ Class is initialized with built-in classes by default.
        """
        super().__init__(*args, **kwds)

    def updateMapping(cls, c={}):
        """ Updates classes mapping.
        Make the package mapping if it has not been made.
        """
        if not cls._package:
            cls.makePackageClasses()
        cls._classes = copy.copy(cls._package)
        cls._classes.update(c)

    def makePackageClasses(cls):
        """ The set of fdi package-wide deserializable classes is maintained by hand.
        Do nothing if the classes mapping is already made so repeated calls will not cost lots more time.
        """

        if cls._package:
            return
        from fdi.dataset.deserialize import deserializeClassID
        from fdi.dataset.finetime import FineTime, FineTime1, utcobj
        from fdi.dataset.baseproduct import History, BaseProduct
        from fdi.dataset.product import Product
        from fdi.dataset.datatypes import Vector, Quaternion
        from fdi.dataset.metadata import Parameter, NumericParameter, MetaData
        from fdi.dataset.dataset import GenericDataset, ArrayDataset, \
            TableDataset, CompositeDataset, Column
        from fdi.pal.context import MapContext, RefContainer, \
            ContextRuleException
        from fdi.pal.urn import Urn
        from fdi.pal.productref import ProductRef

        cls._package = locals()
        return

    # https://stackoverflow.com/a/1800999
    @property
    def mapping(cls):
        """ Returns the dictionary of classes allowed for deserialization, including the fdi built-ins and user added classes.
        """
        if not cls._classes:
            cls.updateMapping()
        return cls._classes

    @mapping.setter
    def mapping(cls, c):
        """ Delegated to cls.updateClasses().
        """
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
