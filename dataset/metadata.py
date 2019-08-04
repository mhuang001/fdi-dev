# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .annotatable import Annotatable
from .copyable import Copyable
from .eq import DeepEqual
from .quantifiable import Quantifiable
from .listener import DatasetEventSender, DatasetBaseListener, ParameterListener, DatasetListener, DatasetEvent, EventType
from .composite import Composite
from .odict import ODict
from .serializable import Serializable
from .datawrapper import DataWrapperMapper


class Parameter(Annotatable, Copyable, DeepEqual, DatasetEventSender, Serializable):
    """ Parameter is the interface for all named attributes
    in the MetaData container. It can have a value and a description."""

    def __init__(self, value=None, type_='', **kwds):
        """ invoked with no argument results in a parameter of
        None value and 'UNKNOWN' description.
        With a signle argument: arg -> value, 'UNKNOWN'-> description.
        With two positional arguments: arg1 -> value, arg2-> description.
        """
        super().__init__(**kwds)
        self.value = value
        self.type_ = type_

    def accept(self, visitor):
        """ Adds functionality to classes of this type."""
        visitor.visit(self)

    def getType(self):
        """ Returns the actual type that is allowed for the value
        of this Parameter."""
        return self.type_

    def setType(self, type_):
        """ Replaces the current type of this parameter. """
        self.type_ = type_

    def getValue(self):
        """ Gets the value of this parameter as an Object. """
        return self.value

    def setValue(self, value):
        """ Replaces the current value of this parameter. """
        self.value = value

    def __setattr__(self, name, value):
        """ add eventhandling """
        super().__setattr__(name, value)

        # this will fail during init when annotatable init sets description
        # if issubclass(self.__class__, DatasetEventSender):
        if 'listeners' in self.__dict__:
            so, ta, ty, ch, ca, ro = self, self, -1, \
                (name, value), None, None
            if name == 'value':
                ty = EventType.VALUE_CHANGED
            elif name == 'unit':
                ty = EventType.UNIT_CHANGED,
            elif name == 'description':
                ty = EventType.DESCRIPTION_CHANGED
            else:
                ty = -1
            e = DatasetEvent(source=so, target=ta, type_=ty,
                             change=ch, cause=ca, rootCause=ro)
            self.fire(e)

    def __repr__(self):
        return self.__class__.__name__ +\
            '{ description = "%s", value = %s, type = %s}' %\
            (str(self.description), str(self.value), str(self.getType()))

    def toString(self):
        return self.__str__()

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(description=self.description,
                     value=self.value,
                     type_=self.type_,
                     classID=self.classID,
                     version=self.version)


class NumericParameter(Parameter, Quantifiable):
    """ has a number as the value and a unit.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ description = "%s", value = "%s", unit = "%s", type = "%s"}' %\
            (str(self.description), str(self.value), self.unit, str(self.getType()))

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(description=self.description,
                     value=self.value,
                     unit=self.unit,
                     type_=self.type_,
                     classID=self.classID,
                     version=self.version)


class MetaData(Composite, Copyable, Serializable, ParameterListener, DatasetEventSender):
    """ A container of named Parameters. A MetaData object can
    have one or more parameters, each of them stored against a
    unique name. The order of adding parameters to this container
    is important, that is: the keySet() method will return a set of
    labels of the parameters in the sequence as they were added.
    Note that replacing a parameter with the same name,
    will keep the order. """

    def __init__(self, copy=None, **kwds):
        super().__init__(**kwds)
        if copy is None:
            return
        else:
            # not implemented ref https://stackoverflow.com/questions/10640642/is-there-a-decent-way-of-creating-a-copy-constructor-in-python
            logger.error('use copy.copy() insteadof MetaData(copy)')

    def accept(self, visitor):
        """ Hook for adding functionality to meta data object
        through visitor pattern."""
        visitor.visit(self)

    def clear(self):
        """ Removes all the key - parameter mappings. """
        self.getDataWrappers().clear()

    def set(self, name, newParameter):
        """ add eventhandling """
        super().set(name, newParameter)

        if 'listeners' in self.__dict__:
            so, ta, ty, ch, ca, ro = self, self, -1, \
                (name, newParameter), None, None
            if name in self.keySet():
                ty = EventType.PARAMETER_CHANGED
            else:
                ty = EventType.PARAMETER_ADDED
            e = DatasetEvent(source=so, target=ta, type_=ty,
                             change=ch, cause=ca, rootCause=ro)
            self.fire(e)

    def remove(self, name):
        """ add eventhandling """
        r = super().remove(name)
        if r is None:
            return r

        if 'listeners' in self.__dict__:
            so, ta, ty, ch, ca, ro = self, self, -1, \
                (name), None, None  # generic initial vals
            ty = EventType.PARAMETER_REMOVED
            ch = (name, r)
            #raise ValueError('Attempt to remove non-existant parameter "%s"' % (name))
            e = DatasetEvent(source=so, target=ta, type_=ty,
                             change=ch, cause=ca, rootCause=ro)
            self.fire(e)
        return r

    def toString(self):
        s, l = '', ''
        for (k, v) in self._sets.items():
            s = s + str(k) + ' = ' + str(v) + ', '
        l = ''.join(['"' + x.description + '", ' for x in self.listeners])
        return self.__class__.__name__ + \
            '{[' + s + '], listeners = [%s]}' % (l)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(_sets=self._sets,
                     classID=self.classID,
                     version=self.version)


class MetaDataHolder(object):
    """ Object holding meta data. 
    mh: object for compatibility with python2
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        # print(self.__dict__)

    def getMeta(self):
        """ Returns the current MetaData container of this object. """
        return self._meta


class Attributable(MetaDataHolder):
    """ An Attributable object is an object that has the
    notion of meta data. """

    def __init__(self, meta=None, **kwds):
        if meta is None:
            self.setMeta(MetaData())
        else:
            self.setMeta(meta)
        super().__init__(**kwds)
        #print('**' + self._meta.toString())

    @property
    def meta(self):
        return self.getMeta()

    @meta.setter
    def meta(self, newMetadata):
        self.setMeta(newMetadata)

    def setMeta(self, newMetadata):
        """ Replaces the current MetaData with specified argument. 
        mh: Product will override this to add listener whenevery meta is
        replaced
        """
        self._meta = newMetadata


class AbstractComposite(Attributable, Annotatable, Composite, DataWrapperMapper, DatasetListener):
    """ an annotatable and attributable subclass of Composite. 
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def __repr__(self):
        ''' meta and datasets only show names
        '''
        s = '{'
        s += 'meta = "%s", _sets = %s}' % (
            str(self.meta),
            str(self.keySet())
        )
        return s

    def toString(self):
        s = '{'
        s += 'meta = %s, _sets = %s}' % (
            self.meta.toString(),
            self._sets.__str__()
        )
        return s
