# -*- coding: utf-8 -*-

from ..utils.masked import masked
from ..utils.common import grouper
from .serializable import Serializable
from .datatypes import DataTypes, DataTypeNames
from .odict import ODict
from .composite import Composite
from .listener import DatasetEventSender, ParameterListener, DatasetListener, DatasetEvent, EventTypeOf
from .quantifiable import Quantifiable
from .eq import DeepEqual
from .copyable import Copyable
from .annotatable import Annotatable
from .finetime import FineTime, FineTime1, utcobj
from .classes import Classes
from .typed import Typed
from .invalid import INVALID
from ..utils.common import exprstrs, wls, mstr

from tabulate import tabulate

import builtins
from collections import OrderedDict
from numbers import Number
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


ParameterClasses = {
    'AbstractParameter': dict(value=None,
                              description='UNKNOWN'),

    'Parameter': dict(value=None,
                      description='UNKNOWN',
                      typ_='',
                      default=None,
                      valid=None),

    'NumericParameter': dict(value=None,
                             description='UNKNOWN',
                             typ_='',
                             unit=None,
                             default=None,
                             valid=None,
                             typecode=None),

    'DateParameter': dict(value=None,
                          description='UNKNOWN',
                          default='',
                          valid=None,
                          typecode=None),

    'StringParameter': dict(value=None,
                            description='UNKNOWN',
                            default='',
                            valid=None,
                            typecode='B'),

}


def parameterDataClasses(tt):
    """ maps machine type names to class objects """
    if tt not in DataTypeNames:
        raise TypeError("Type %s is not in %s." %
                        (tt, str([''.join(x) for x in DataTypeNames])))
    if tt == 'int':
        return int
    elif tt in builtins.__dict__:
        return builtins.__dict__[tt]
    else:
        return Classes.mapping[tt]


class AbstractParameter(Annotatable, Copyable, DeepEqual, DatasetEventSender, Serializable):
    """ Parameter is the interface for all named attributes
    in the MetaData container. It can have a value and a description.
    Default     value=None, description='UNKNOWN'
    """

    def __init__(self, value=None, description='UNKNOWN', **kwds):
        """ Constructed with no argument results in a parameter of
        None value and 'UNKNOWN' description ''.
        With a signle argument: arg -> value, 'UNKNOWN' as default-> description.
        With two positional arguments: arg1-> value, arg2-> description.
        Type is set according to value's.
        Unsuported parameter types will get a NotImplementedError.
        """
        super(AbstractParameter, self).__init__(
            description=description, **kwds)

        self.setValue(value)

    def accept(self, visitor):
        """ Adds functionality to classes of this type."""
        visitor.visit(self)

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
        """
        self._value = value

    def __setattr__(self, name, value):
        """ add eventhandling """
        super(AbstractParameter, self).__setattr__(name, value)

        # this will fail during init when annotatable init sets description
        # if issubclass(self.__class__, DatasetEventSender):
        if 'listeners' in self.__dict__:
            so, ta, ty, ch, ca, ro = self, self, \
                EventType.UNKNOWN_ATTRIBUTE_CHANGED, \
                (name, value), None, None

            nu = name.upper()
            if nu in EventTypeOf['CHANGED']:
                ty = EventTypeOf['CHANGED'][nu]
            else:
                tv = EventType.UNKNOWN_ATTRIBUTE_CHANGED
            e = DatasetEvent(source=so, target=ta, typ_=ty,
                             change=ch, cause=ca, rootCause=ro)
            self.fire(e)

#    def ff(self, name, value):
#
#        if eventType is not None:
#            if eventType not in EventType:
#                # return eventType
#                raise ValueError(str(eventType))
#            elif eventType != EventType.UNKOWN_ATTRIBUTE_CHANGED:
#                # super() has found the type
#                return eventType
#        # eventType is None or is UNKOWN_ATTRIBUTE_CHANGED
#            if name == 'value':
#                ty = EventType.VALUE_CHANGED
#                ch = (value)
#            elif name == 'description':
#                ty = EventType.DESCRIPTION_CHANGED
#            else:
#                # raise AttributeError(
#                #    'Parameter "'+self.description + '" has no attribute named '+name)
#                pass
#            if ty != EventType.UNKOWN_ATTRIBUTE_CHANGED:
#                e = DatasetEvent(source=so, target=ta, typ_=ty,
#                                 change=ch, cause=ca, rootCause=ro)
#                self.fire(e)
#            return ty
#        return eventType
#
    def equals(self, obj):
        """ can compare value """
        if type(obj).__name__ in DataTypes.values():
            return self.value == obj
        else:
            return super(AbstractParameter, self).equals(obj)

    def __lt__(self, obj):
        """ can compare value """
        if type(obj).__name__ in DataTypes.values():
            return self.value < obj
        else:
            return super(AbstractParameter, self).__lt__(obj)

    def __gt__(self, obj):
        """ can compare value """
        if type(obj).__name__ in DataTypes.values():
            return self.value > obj
        else:
            return super(AbstractParameter, self).__gt__(obj)

    def __le__(self, obj):
        """ can compare value """
        if type(obj).__name__ in DataTypes.values():
            return self.value <= obj
        else:
            return super(AbstractParameter, self).__le__(obj)

    def __ge__(self, obj):
        """ can compare value """
        if type(obj).__name__ in DataTypes.values():
            return self.value >= obj
        else:
            return super(AbstractParameter, self).__ge__(obj)

    def getValueAsString():
        """ Value as string for building the string representation of the parameter.  """
        return

    def __repr__(self):
        return self.toString(level=1)

    def toString(self, level=0, alist=False, **kwds):
        """ alist: returns a dictionary string representation of parameter attributes.
        """
        vs = str(self._value)
        ds = str(self.description)
        ss = '%s' % (vs) if level else \
            '%s, "%s"' % (vs, ds)
        if alist:
            return exprstrs(self)
        return self.__class__.__name__ + ss

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           value=self.value,
                           listeners=self.listeners,
                           _STID=self._STID
                           )


class Parameter(AbstractParameter, Typed):
    """ Parameter is the interface for all named attributes
    in the MetaData container. It can have a value and a description.
    Defaul arguments: typ_='', default=None, valid=None.
    value=default, description='UNKNOWN'
    """

    def __init__(self, value=None, description='UNKNOWN', typ_='', default=None, valid=None, **kwds):
        """ invoked with no argument results in a parameter of
        None value and 'UNKNOWN' description ''. typ_ DataTypes[''], which is None.
        With a signle argument: arg -> value, 'UNKNOWN'-> description. ParameterTypes-> typ_, hex values have integer typ_.
        Unsuported parameter types will get a NotImplementedError.
f        With two positional arguments: arg1-> value, arg2-> description. ParameterTypes['']-> typ_.
        Unsuported parameter types will get a NotImplementedError.
        With three positional arguments: arg1 casted to DataTypes[arg3]-> value, arg2-> description. arg3-> typ_.
        Unsuported parameter types will get a NotImplementedError.
        Incompatible value and typ_ will get a TypeError.
        """
        # super(Parameter, self).__init__(description=description, **kwds)

        self.setDefault(default)
        self.setValid(valid)
        # super() will set value so type and default need to be set first
        super(Parameter, self).__init__(
            value=value, description=description, typ_=typ_, **kwds)

    def accept(self, visitor):
        """ Adds functionality to classes of this type."""
        visitor.visit(self)

    def setType(self, typ_):
        """ Replaces the current type of this parameter.
        Defaul will be casted if not the same.
        Unsuported parameter types will get a NotImplementedError.
        """
        if typ_ is None or typ_ == '':
            self._type = ''
            return
        if typ_ in DataTypes:
            super().setType(typ_)
            # let setdefault deal with type
            self.setDefault(self._default)
        else:
            raise NotImplementedError(
                'Parameter type %s is not in %s.' %
                (typ_, str([''.join(x) for x in DataTypes])))

    def checked(self, value):
        """ Checks input value against self.type.

        If value is none, returns it;
        else if type is not set, return value after setting type;
        If value's type is a subclass of self's type, return the value;
        If value's and self's types are both subclass of Number, returns value casted in self's type.
        """
        if not hasattr(self, '_type'):

            return value

        t_type = type(value)
        t = t_type.__name__
        st = self._type
        if st == '' or st is None:
            # self does not have a type
            try:
                ct = DataTypeNames[t]
                if ct == 'vector':
                    self._type = 'quaternion' if len(value) == 4 else ct
                else:
                    self._type = ct
            except KeyError as e:
                raise TypeError("Type %s is not in %s." %
                                (t, str([''.join(x) for x in DataTypeNames])))
            return value

        # self has type
        tt = DataTypes[st]
        if tt in Classes.mapping:
            # custom-defined parameter. delegate checking to themselves
            return value
        tt_type = builtins.__dict__[tt]
        if issubclass(t_type, tt_type):
            return value
        elif issubclass(t_type, Number) and issubclass(tt_type, Number):
            # , if both are Numbers.Number, value is casted into given typ_.
            return tt_type(value)
            # st = tt
        else:
            vs = hex(value) if t == 'int' and st == 'hex' else str(value)
            raise TypeError(
                'Value %s is of type %s, but should be %s.' % (vs, t, tt))

    @property
    def default(self):
        return self.getDefault()

    @default.setter
    def default(self, default):
        self.setDefault(default)

    def getDefault(self):
        """ Returns the default related to this object."""
        return self._default

    def setDefault(self, default):
        """ Sets the default of this object.

        Default is set directly if type is not set or default is None.
        If the type of default is not getType(), TypeError is raised.
        """

        if default is None:
            self._default = default
            return

        self._default = self.checked(default)

    @property
    def valid(self):
        return self.getValid()

    @valid.setter
    def valid(self, valid):
        self.setValid(valid)

    def getValid(self):
        """ Returns the valid related to this object."""
        return self._valid

    def setValid(self, valid):
        """ Sets the valid of this object.

        If valid is None or empty, set as None, else save in a way so the tuple keys can be serialized with JSON.
        """
        def t2l(t):
            """ convert tuples to lists in nested data structures
            """
            # print(t)
            if issubclass(t.__class__, (list, tuple)):
                lst = [t2l(x) if issubclass(
                    x.__class__, tuple) else x for x in t]
                # print('== ', lst)
                return lst
            return t

        self._valid = None if valid is None or len(
            valid) == 0 else [t2l([k, v]) for k, v in valid.items()] if issubclass(valid.__class__, dict) else t2l(valid)

    def isvalid(self):
        res = self.validate(self.value)
        if issubclass(res.__class__, tuple):
            return res[0] is not INVALID
        else:
            return True

    def validate(self, value):
        """ checks if a match the rule set.

        returns:
        (valid value, rule name) for discrete and range rules.
        dictionary of key=mask, val=(valid val, rule name) tuple for binary masks rules.
        (INVALID, 'Invalid') if no matching is found.
        (value, 'Default') if rule set is empty.
        """
        ruleset = self.getValid()
        if ruleset is None or len(ruleset) == 0:
            return (value, 'Default')

        st = DataTypes[self._type]
        vt = type(value).__name__

        if st is not None and st != '' and vt != st:
            return (INVALID, 'Type '+vt)

        binmasks = {}
        hasvalid = False
        for rn in ruleset:
            rule, name = tuple(rn)
            res = INVALID
            if issubclass(rule.__class__, (tuple, list)):
                if rule[0] is Ellipsis:
                    res = INVALID if (value > rule[1]) else value
                elif rule[1] is Ellipsis:
                    res = INVALID if (value < rule[0]) else value
                elif rule[0] >= rule[1]:
                    # binary masked rules are [mask, vld] e.g. [0B011000,0b11]
                    mask, vld = rule[0], rule[1]
                    if len(binmasks.setdefault(mask, [])) == 0:
                        if masked(value, mask) == vld:
                            # record, indexed by mask
                            binmasks[mask] += [vld, name]
                else:
                    # range
                    res = INVALID if (value < rule[0]) or (
                        value > rule[1]) else value
            else:
                # discrete value
                res = value if rule == value else INVALID
            if not hasvalid:
                # record the 1st valid
                if res is not INVALID:
                    hasvalid = (res, name)
        if any(len(resnm) for mask, resnm in binmasks.items()):
            return [tuple(resnm) if len(resnm) else (INVALID, 'Invalid') for mask, resnm in binmasks.items()]
        return hasvalid if hasvalid else (INVALID, 'Invalid')

    def setValue(self, value):
        """ Replaces the current value of this parameter.

        If value is None set it to default.
        If given/current type is '' and arg value's type is in DataTypes both value and type are updated to the suitable one in DataTypeNames; or else TypeError is raised.
        If value type and given/current type are different.
            Incompatible value and type will get a TypeError.
        """

        if value is None:
            self._value = self._default if hasattr(self, '_default') else value
            return
        self._value = self.checked(value)

    def __repr__(self):
        return self.toString(level=1)

    def toString(self, level=0, alist=False, **kwds):

        ret = exprstrs(self, level=level, **kwds)
        if alist:
            return ret
        vs, us, ts, ds, fs, gs, cs = ret
        if level:
            return vs
        return '%s{ %s <%s>, "%s", default= %s, valid= %s tcode=%s}' % \
            (self.__class__.__name__, vs, ts, ds, fs, gs, cs)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           value=self._value,
                           type=self._type,
                           default=self._default,
                           valid=self._valid,
                           listeners=self.listeners,
                           _STID=self._STID
                           )


class NumericParameter(Parameter, Quantifiable):
    """ has a number as the value, a unit, and a typecode.
    """

    def __init__(self, value=None, description='UNKNOWN', typ_='', default=None, valid=None, **kwds):
        super(NumericParameter, self).__init__(
            value=value, description=description, typ_=typ_, default=default, valid=valid, **kwds)

    def __repr__(self):
        return self.toString(level=1)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           value=self._value,
                           type=self._type,
                           default=self._default,
                           valid=self._valid,
                           unit=self._unit,
                           typecode=self._typecode,
                           _STID=self._STID)


class DateParameter(Parameter):
    """ has a FineTime as the value.
    """

    def __init__(self, value=None, description='UNKNOWN', default=0, valid=None, typecode=None, **kwds):
        """
        if value and typecode are both given, typecode will be overwritten by value.format.
        """
        self.setTypecode(typecode)
        # this will set default then set value.
        super(DateParameter, self).__init__(
            value=value, description=description, typ_='finetime', default=default, valid=valid, **kwds)

    @ property
    def typecode(self):
        return self.getTypecode()

    @ typecode.setter
    def typecode(self, typecode):
        self.setTypecode(typecode)

    def getTypecode(self):
        """ Returns the typecode related to this object. None if value not set."""
        if not hasattr(self, '_value'):
            return None
        return self._value.format

    def setTypecode(self, typecode):
        """ Sets the typecode of this object. quietly returns if value not set."""
        if not hasattr(self, '_value'):
            return
        self._value.format = typecode

    def setValue(self, value):
        """ accept any type that a FineTime does.
        """
        if value is not None and not issubclass(value.__class__, FineTime):
            value = FineTime(date=value, format=self.getTypecode())
        super().setValue(value)

    def setDefault(self, default):
        """ accept any type that a FineTime does.
        """
        if default is not None and not issubclass(default.__class__, FineTime):
            default = FineTime(date=default, format=self.getTypecode())
        super().setDefault(default)

    def __repr__(self):

        return self.toString(level=1)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(description=self.description,
                           value=self._value,
                           default=self._default,
                           valid=self._valid,
                           typecode=self.typecode,
                           _STID=self._STID)
        return self.__class__.__name__ + \
            '{ description = "%s", value = "%s", typecode = "%s"}' % \
            (str(self.description), str(self.value), str(self.getTypecode()))


class DateParameter1(DateParameter):
    """ Like DateParameter but usese  FineTime. """

    def setValue(self, value):
        """ accept any type that a FineTime1 does.
        """
        if value is not None and not issubclass(value.__class__, FineTime1):
            value = FineTime1(date=value, format=self.getTypecode())
        super().setValue(value)

    def setDefault(self, default):
        """ accept any type that a FineTime1 does.
        """
        if default is not None and not issubclass(default.__class__, FineTime1):
            default = FineTime1(date=default, format=self.getTypecode())
        super().setDefault(default)


class StringParameter(Parameter):
    """ has a unicode string as the value, a typecode for length and char.
    """

    def __init__(self, value=None, description='UNKNOWN', valid=None, default='', typecode='B', **kwds):
        self.setTypecode(typecode)
        super(StringParameter, self).__init__(
            value=value, description=description, typ_='string', default=default, valid=valid, **kwds)

    @ property
    def typecode(self):
        return self.getTypecode()

    @ typecode.setter
    def typecode(self, typecode):
        self.setTypecode(typecode)

    def getTypecode(self):
        """ Returns the typecode related to this object."""
        return self._typecode

    def setTypecode(self, typecode):
        """ Sets the typecode of this object. """
        self._typecode = typecode

    def __repr__(self):
        return self.toString(level=1)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return OrderedDict(value=self._value,
                           description=self.description,
                           valid=self._valid,
                           default=self._default,
                           typecode=self._typecode,
                           _STID=self._STID)


MetaHeaders = ['name', 'value', 'unit', 'type', 'valid',
               'default', 'code', 'description']


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
        if not issubclass(newParameter.__class__, AbstractParameter):
            raise TypeError('Only Parameters can be saved.')

        super(MetaData, self).set(name, newParameter)

        if 'listeners' in self.__dict__:
            so, ta, ty, ch, ca, ro = self, self, -1, \
                (name, newParameter), None, None
            if name in self.keySet():
                ty = EventType.PARAMETER_CHANGED
            else:
                ty = EventType.PARAMETER_ADDED
            e = DatasetEvent(source=so, target=ta, typ_=ty,
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
            e = DatasetEvent(source=so, target=ta, typ_=ty,
                             change=ch, cause=ca, rootCause=ro)
            self.fire(e)
        return r

    def toString(self, level=0, tablefmt='grid', tablefmt1='simple', **kwds):

        l = self.listeners.toString(level=level, **kwds)
        tab = []
        # N parameters per row for level 1
        N = 3
        i, row = 0, []
        cn = self.__class__.__name__
        s = ''
        for (k, v) in self._sets.items():
            pk = str(k)
            vs, us, ts, ds, fs, gs, cs = v.toString(alist=True)
            # print(vs, us, ts, ds, fs, gs, cs)
            if level == 0:
                vw = 17  # -1 if ts == 'finetime' else 17
                tab.append((wls(pk, 14), wls(vs, vw), wls(us, 7),
                            wls(ts, 8), wls(gs, 20), wls(fs, vw),
                            wls(cs, 4), wls(ds, 17)))
            elif level == 1:
                ps = '%s= %s' % (pk, vs)
                # s += mstr(self, level=level, depth=1, tablefmt=tablefmt, **kwds)
                tab.append(wls(ps, 80//N))
                if 0:
                    row.append(wls(ps, 80//N))
                    i += 1
                    if i == N:
                        tab.append(row)
                        i, row = 0, []
            else:
                tab.append(pk)

        if level == 0:
            headers = MetaHeaders
            fmt = tablefmt
            s += tabulate(tab, headers=headers, tablefmt=fmt, missingval='',
                          disable_numparse=True) if len(tab) else '(empty)'
        elif level == 1:
            t = grouper(tab, N)
            headers = ''
            fmt = tablefmt1
            s += tabulate(t, headers=headers, tablefmt=fmt, missingval='',
                          disable_numparse=True) if len(tab) else '(empty)'
        else:
            s += ', '.join(tab)
            return '%s, listeners = %s' % (s, l)
        return '\n%s\n%s-listeners = %s' % (s, cn, l)

    def __repr__(self, **kwds):
        return self.toString(level=1, **kwds)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        # print(self.listeners)
        # print([id(o) for o in self.listeners])

        return OrderedDict(_sets=self._sets,
                           listeners=self.listeners,
                           _STID=self._STID)
