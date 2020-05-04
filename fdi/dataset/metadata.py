# -*- coding: utf-8 -*-

from numbers import Number
from collections import OrderedDict
from .serializable import Serializable
from .odict import ODict
from .composite import Composite
from .listener import DatasetEventSender, ParameterListener, DatasetListener, DatasetEvent, EventType
from .quantifiable import Quantifiable
from .eq import DeepEqual
from .copyable import Copyable
from .annotatable import Annotatable

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

""" Allowed Parameter types and the corresponding classes.
The keys are mnemonics for humans; the values are type(x).__name__.
"""
ParameterTypes = {
    'integer': 'int',
    'hex': 'int',
    'float': 'float',
    'string': 'str',
    'finetime': 'FineTime1',
    'baseProduct': 'BaseProduct',
    'mapContext': 'MapContext',
    'product': 'Product',
    'vector': 'Vector',
    'quaternion': 'Quaternion',
    '': 'None'
}


class Parameter(Annotatable, Copyable, DeepEqual, DatasetEventSender, Serializable):
    """ Parameter is the interface for all named attributes
    in the MetaData container. It can have a value and a description."""

    def __init__(self, value=None, description='UNKNOWN', type_='', **kwds):
        """ invoked with no argument results in a parameter of
        None value and 'UNKNOWN' description ''. type_ ParameterTypes[''], which is None.
        With a signle argument: arg -> value, 'UNKNOWN'-> description. ParameterTypes-> type_, hex values have integer type_.
        Unsuported parameter types will get a NotImplementedError.
f        With two positional arguments: arg1-> value, arg2-> description. ParameterTypes['']-> type_.
        Unsuported parameter types will get a NotImplementedError.
        With three positional arguments: arg1 casted to ParameterTypes[arg3]-> value, arg2-> description. arg3-> type_.
        Unsuported parameter types will get a NotImplementedError.
        Incompatible value and type_ will get a TypeError.
        """
        super(Parameter, self).__init__(description=description, **kwds)

        self.setType(type_)
        self.setValue(value)

    def accept(self, visitor):
        """ Adds functionality to classes of this type."""
        visitor.visit(self)

    @property
    def type_(self):
        """ for property getter
        """
        return self.getType()

    @type_.setter
    def type_(self, type_):
        """ for property setter
        """
        self.setType(type_)

    def getType(self):
        """ Returns the actual type that is allowed for the value
        of this Parameter."""
        return self._type

    def setType(self, type_):
        """ Replaces the current type of this parameter.
        Unsuported parameter types will get a NotImplementedError.
        """
        if type_ in ParameterTypes:
            self._type = type_
        else:
            raise NotImplementedError(
                'Parameter type %s is not in %s.' %
                (type_, str([''.join(x) for x in ParameterTypes])))

    @property
    def value(self):
        """ for property getter
        """
        return self.getValue()

    @value.setter
    def value(self, value):
        """ for property setter
        """
        self.setValue(value)

    def getValue(self):
        """ Gets the value of this parameter as an Object. """
        return self._value

    def setValue(self, value):
        """ Replaces the current value of this parameter. 
        If given/current type_ is '' and arg value's type is in ParameterTypes both value and type are updated; or else TypeError is raised.
        If value type and given/current type_ are different.
            Incompatible value and type_ will get a TypeError.
        """
        t = type(value).__name__

        if self._type == '':
            if value is None:
                self._value = value
                return
            else:
                if t in ParameterTypes.values():
                    self._value = value
                    self._type = [name for name,
                                  ty in ParameterTypes.items() if ty == t][0]
                    return
                else:
                    raise TypeError('Value type %s is not in %s.' %
                                    (t, str([''.join(x) for x in ParameterTypes])))
        tt = ParameterTypes[self._type]
        if t == tt:  # TODO: subclass
            self._value = value
        elif 0 and issubclass(t, Number) and issubclass(tt, Number):
            # , if both are Numbers.Number, value is casted into given type_.
            self._value = tt(value)
            #self._type = tt.__name__
        else:
            vs = hex(value) if t == 'int' and self._type == 'hex' else str(value)
            raise TypeError('Value %s type is %s, not %s.' % (vs, t, tt))

    def __setattr__(self, name, value):
        """ add eventhandling """
        super(Parameter, self).__setattr__(name, value)

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
        vs = hex(self._value) if self._type == 'hex' and issubclass(
            self._value.__class__, int) else str(self._value)
        return self.__class__.__name__ +\
            '{ %s <%s>, "%s"}' %\
            (vs, str(self._type), str(self.description))

    def toString(self):
        return self.__str__()

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(description=self.description,
                     value=self.value,
                     listeners=self.listeners,
                     type_=self.type_,
                     classID=self.classID,
                     version=self.version)


class NumericParameter(Parameter, Quantifiable):
    """ has a number as the value and a unit.
    """

    def __init__(self, **kwds):
        super(NumericParameter, self).__init__(**kwds)

    def __repr__(self):
        vs = hex(self._value) if self._type == 'hex' and issubclass(
            self._value.__class__, int) else str(self._value)
        return self.__class__.__name__ + \
            '{ %s (%s) <%s>, "%s"}' %\
            (vs, self.unit, str(self._type), str(self.description))

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(description=self.description,
                     value=self.value,
                     unit=self.unit,
                     type_=self.type_,
                     classID=self.classID,
                     version=self.version)


class StringParameter(Parameter):
    """ has a unicode string as the value.
    """

    def __init__(self, **kwds):
        super(StringParameter, self).__init__(**kwds)

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ description = "%s", value = "%s", type = "%s"}' %\
            (str(self.description), str(self.value), str(self.getType()))

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(description=self.description,
                     value=self.value,
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
        super(MetaData, self).__init__(**kwds)
        if copy:
            # not implemented ref https://stackoverflow.com/questions/10640642/is-there-a-decent-way-of-creating-a-copy-constructor-in-python
            logger.error('use copy.copy() insteadof MetaData(copy)')
        else:
            return

    def accept(self, visitor):
        """ Hook for adding functionality to meta data object
        through visitor pattern."""
        visitor.visit(self)

    def clear(self):
        """ Removes all the key - parameter mappings. """
        self.getDataWrappers().clear()

    def set(self, name, newParameter):
        """ Saves the parameter and  add eventhandling.
        Raises TypeError if not given Parameter (sub) class object.
        """
        if not issubclass(newParameter.__class__, Parameter):
            raise TypeError('Only Parameters can be saved.')

        super(MetaData, self).set(name, newParameter)

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
        r = super(MetaData, self).remove(name)
        if r is None:
            return r

        if 'listeners' in self.__dict__:
            so, ta, ty, ch, ca, ro = self, self, -1, \
                (name), None, None  # generic initial vals
            ty = EventType.PARAMETER_REMOVED
            ch = (name, r)
            # raise ValueError('Attempt to remove non-existant parameter "%s"' % (name))
            e = DatasetEvent(source=so, target=ta, type_=ty,
                             change=ch, cause=ca, rootCause=ro)
            self.fire(e)
        return r

    def toString(self):
        s, l = '', ''
        for (k, v) in self._sets.items():
            s = s + str(k) + ' = ' + str(v) + ', '
        l = ''.join([x.__class__.__name__ + ' ' + str(id(x)) +
                     ' "' + x.description + '", ' for x in self.listeners])
        return self.__class__.__name__ + \
            '{[' + s + '], listeners = [%s]}' % (l)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        # print(self.listeners)
        # print([id(o) for o in self.listeners])

        return ODict(_sets=self._sets,
                     listeners=self.listeners,
                     classID=self.classID,
                     version=self.version)
