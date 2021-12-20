# -*- coding: utf-8 -*-

from .serializable import Serializable
from .datatypes import DataTypes, DataTypeNames
from .odict import ODict
from .composite import Composite
from .listener import DatasetEventSender, ParameterListener, DatasetEvent, EventTypeOf
from .eq import DeepEqual, xhash
from .copyable import Copyable
from .annotatable import Annotatable
from .classes import Classes
from .typed import Typed
from .invalid import INVALID
from ..utils.masked import masked
from ..utils.common import grouper
from ..utils.common import exprstrs, wls, bstr, t2l


import cwcwidth as wcwidth
import tabulate

from itertools import zip_longest, filterfalse
import builtins
from collections import OrderedDict, UserList
from numbers import Number
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

tabulate.wcwidth = wcwidth
tabulate.WIDE_CHARS_MODE = True
tabulate.MIN_PADDING = 0
#tabulate.PRESERVE_WHITESPACE = True
Default_Extra_Param_Width = 10

"""
| Attribute | Defining Module | Holder Variable |
| 'description' | `Annotatable` | `description` |
| 'typ_' | `Typed` | `_type` |
| 'unit' | `Quantifiable` | '_unit' |
| 'typecode' | `Typecoded` | '_typecode' |
"""
Parameter_Attr_Defaults = {
    'AbstractParameter': dict(
        value=None,
        description='UNKNOWN'
    ),

    'Parameter': dict(
        value=None,
        description='UNKNOWN',
        typ_='',
        default=None,
        valid=None
    ),

    'NumericParameter': dict(
        value=None,
        description='UNKNOWN',
        typ_='',
        default=None,
        unit=None,
        valid=None,
        typecode=None
    ),

    'BooleanParameter': dict(
        value=None,
        description='UNKNOWN',
        typ_='',
        default=None,
        valid=None,
    ),

    'DateParameter': dict(
        value=None,
        description='UNKNOWN',
        typ_='',
        default=0,
        valid=None,
    ),

    'StringParameter': dict(
        value=None,
        description='UNKNOWN',
        typ_='',
        default='',
        valid=None,
        typecode=None
    ),

}


def parameterDataClasses(tt):
    """ maps machine type names to class objects
    Parameters
    ----------

    Returns
    -------

    """
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
    in the MetaData container.

    A Parameter is a variable with associated information about its description, unit, type, valid ranges, default, format code etc. Type can be numeric, string, datetime, vector.

    Often a parameter shows a property. So a parameter in the metadata of a dataset or product is often called a property.

    Default     value=None, description='UNKNOWN'
    """

    def __init__(self,
                 value=None,
                 description='UNKNOWN',
                 **kwds):
        """ Constructed with no argument results in a parameter of
        None value and 'UNKNOWN' description ''.
        With a signle argument: arg -> value, 'UNKNOWN' as default-> description.
        With two positional arguments: arg1-> value, arg2-> description.
        Type is set according to value's.
        Unsuported parameter types will get a NotImplementedError.
        Parameters
        ----------

        Returns
        -------
        """

        super().__init__(description=description, **kwds)

        self.setValue(value)
        self._defaults = Parameter_Attr_Defaults[self.__class__.__name__]

    def accept(self, visitor):
        """ Adds functionality to classes of this type.
        Parameters
        ----------

        Returns
        -------

        """
        visitor.visit(self)

    @property
    def value(self):
        """ for property getter
        Parameters
        ----------

        Returns
        -------

        """
        return self.getValue()

    @value.setter
    def value(self, value):
        """ for property setter
        Parameters
        ----------

        Returns
        -------

        """
        self.setValue(value)

    def getValue(self):
        """ Gets the value of this parameter as an Object.
        Parameters
        ----------

        Returns
        -------
        """
        return self._value

    def setValue(self, value):
        """ Replaces the current value of this parameter.
        Parameters
        ----------

        Returns
        -------

        """
        self._value = value

    def __setattr__(self, name, value):
        """ add eventhandling
        Parameters
        ----------

        Returns
        -------

        """
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
    def __eq__(self, obj, verbose=False, **kwds):
        """ can compare value
        Parameters
        ----------

        Returns
        -------

        """
        if type(obj).__name__ in DataTypes.values():
            return self.value == obj
        else:
            return super(AbstractParameter, self).__eq__(obj)

    def __lt__(self, obj):
        """ can compare value
        Parameters
        ----------

        Returns
        -------

        """
        if type(obj).__name__ in DataTypes.values():
            return self.value < obj
        else:
            return super(AbstractParameter, self).__lt__(obj)

    def __gt__(self, obj):
        """ can compare value
        Parameters
        ----------

        Returns
        -------

        """
        if type(obj).__name__ in DataTypes.values():
            return self.value > obj
        else:
            return super(AbstractParameter, self).__gt__(obj)

    def __le__(self, obj):
        """ can compare value
        Parameters
        ----------

        Returns
        -------
        """
        if type(obj).__name__ in DataTypes.values():
            return self.value <= obj
        else:
            return super(AbstractParameter, self).__le__(obj)

    def __ge__(self, obj):
        """ can compare value
        Parameters
        ----------

        Returns
        -------
        """
        if type(obj).__name__ in DataTypes.values():
            return self.value >= obj
        else:
            return super(AbstractParameter, self).__ge__(obj)

    def getValueAsString():
        """ Value as string for building the string representation of the parameter.
        Parameters
        ----------

        Returns
        -------

        """
        return

    def hash(self):
        """ hash and equality derived only from the value of the parameter.

        because Python does not allow overriding __eq__ without setting hash to None.
        """
        return xhash(hash_list=self._value)

    def toString(self, level=0, alist=False, **kwds):
        """ alist: returns a dictionary string representation of parameter attributes.
        Parameters
        ----------

        Returns
        -------

        """
        vs = str(self._value)
        ds = str(self.description)
        ss = '%s' % (vs) if level else \
            '%s, "%s"' % (vs, ds)
        if alist:
            return exprstrs(self, **kwds)
        return self.__class__.__name__ + ss

    string = toString

    def __getstate__(self):
        """ Can be encoded with serializableEncoder
        Parameters
        ----------

        Returns
        -------

        """
        return OrderedDict(description=self.description,
                           value=self.value,
                           listeners=self.listeners
                           )


def make_jsonable(valid):

    return[t2l([k, v]) for k, v in valid.items()] if issubclass(valid.__class__, dict) else t2l(valid)


Seqs = (list, tuple, UserList)


class Parameter(AbstractParameter, Typed):
    """ Parameter is the interface for all named attributes
    in the MetaData container. It can have a value and a description.
    Default arguments: typ_='', default=None, valid=None.
    value=default, description='UNKNOWN'
    """

    def __init__(self,
                 value=None,
                 description='UNKNOWN',
                 typ_='',
                 default=None,
                 valid=None,
                 **kwds):
        """ invoked with no argument results in a parameter of
        None value and 'UNKNOWN' description ''. typ_ DataTypes[''], which is None.
        With a signle argument: arg -> value, 'UNKNOWN'-> description. ParameterTypes-> typ_, hex values have integer typ_.
        Unsuported parameter types will get a NotImplementedError.
f        With two positional arguments: arg1-> value, arg2-> description. ParameterTypes['']-> typ_.
        Unsuported parameter types will get a NotImplementedError.
        With three positional arguments: arg1 casted to DataTypes[arg3]-> value, arg2-> description. arg3-> typ_.
        Unsuported parameter types will get a NotImplementedError.
        Incompatible value and typ_ will get a TypeError.
        Parameters
        ----------

        Returns
        -------

        """

        # collect args-turned-local-variables.
        args = OrderedDict(filterfalse(
            lambda x: x[0] in ('self', '__class__', 'kwds'),
            locals().items())
        )
        args.update(kwds)
        self._all_attrs = args

        self.setDefault(default)
        self.setValid(valid)
        # super() will set value so type and default need to be set first

        super().__init__(value=value, description=description, typ_=typ_, **kwds)

    def accept(self, visitor):
        """ Adds functionality to classes of this type.
        Parameters
        ----------

        Returns
        -------

        """
        visitor.visit(self)

    def setType(self, typ_):
        """ Replaces the current type of this parameter.

        Default will be casted if not the same.
        Unsuported parameter types will get a NotImplementedError.
        Parameters
        ----------

        Returns
        -------

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
        Parameters
        ----------

        Returns
        -------

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
            if issubclass(type(value), tuple):
                # frozendict used in baseproduct module change lists to tuples
                # which causes deserialized parameter to differ from ProductInfo.
                value = list(value)
            return value
        tt_type = builtins.__dict__[tt]
        if issubclass(t_type, tt_type):
            return value
        elif issubclass(t_type, Number) and issubclass(tt_type, Number):
            # , if both are Numbers.Number, value is casted into given typ_.
            return tt_type(value)
            # st = tt
        elif issubclass(t_type, Seqs) and issubclass(tt_type, Seqs):
            # , if both are Numbers.Number, value is casted into given typ_.
            return tt_type(value)
            # st = tt
        else:
            vs = hex(value) if t == 'int' and st == 'hex' else str(value)
            raise TypeError(
                'Value %s is of type %s, but should be %s.' % (vs, t, tt))

    def setValue(self, value):
        """ Replaces the current value of this parameter.

        If value is None set it to None (#TODO: default?)
        If given/current type is '' and arg value's type is in DataTypes both value and type are updated to the suitable one in DataTypeNames; or else TypeError is raised.
        If value type is not a subclass of given/current type, or
            Incompatible value and type will get a TypeError.
        """

        if value is None:
            v = self._default if hasattr(self, '_default') else value
        else:
            v = self.checked(value)
        super().setValue(v)

    @ property
    def default(self):
        """
        Parameters
        ----------

        Returns
        -------
        """
        return self.getDefault()

    @ default.setter
    def default(self, default):
        """
        Parameters
        ----------

        Returns
        -------
        """

        self.setDefault(default)

    def getDefault(self):
        """ Returns the default related to this object.
        Parameters
        ----------

        Returns
        -------
        """
        return self._default

    def setDefault(self, default):
        """ Sets the default of this object.

        Default is set directly if type is not set or default is None.
        If the type of default is not getType(), TypeError is raised.

        Parameters
        ----------

        Returns
        -------
        """

        if default is None:
            self._default = default
            return

        self._default = self.checked(default)

    @ property
    def valid(self):
        """
        Parameters
        ----------

        Returns
        -------
        """
        return self.getValid()

    @ valid.setter
    def valid(self, valid):
        """
        Parameters
        ----------

        Returns
        -------
        """

        self.setValid(valid)

    def getValid(self):
        """ Returns the valid related to this object.
        Parameters
        ----------

        Returns
        -------
        """
        return self._valid

    def setValid(self, valid):
        """ Sets the valid of this object.

        If valid is None or empty, set as None, else save in a way so the tuple keys can be serialized with JSON. [[[rangelow, ranehi], state1], [[range2low, r..]..]..]

        Parameters
        ----------

        Returns
        -------
        """

        self._valid = None if valid is None or len(
            valid) == 0 else make_jsonable(valid)

    def isValid(self):
        """
        Parameters
        ----------

        Returns
        -------
        """

        res = self.validate(self.value)
        if issubclass(res.__class__, tuple):
            return res[0] is not INVALID
        else:
            return True

    def split(self, into=None):
        """ split a multiple binary bit-masked parameters according to masks.

        into: dictionary mapping bit-masks to the sub-name of the parameter.
        return: a dictionary mapping name of new parameters to its value.
        Parameters
        ----------

        Returns
        -------
        """
        ruleset = self.getValid()
        if ruleset is None or len(ruleset) == 0:
            return {}

        st = DataTypes[self._type]
        vt = type(self._value).__name__

        if st is not None and st != '' and vt != st:
            return {}

        masks = {}
        # number of bits of mask
        highest = 0
        for rn in ruleset:
            rule, name = tuple(rn)
            if issubclass(rule.__class__, (tuple, list)):
                if rule[0] is Ellipsis or rule[1] is Ellipsis:
                    continue
                if rule[0] >= rule[1]:
                    # binary masked rules are [mask, vld] e.g. [0B011000,0b11]
                    mask, valid_val = rule[0], rule[1]
                    masked_val, mask_height, mask_width = masked(
                        self._value, mask)
                    masks[mask] = masked_val
                    if mask_height > highest:
                        highest = mask_height

        if into is None or len(into) < len(masks):
            # like {'0b110000': 0b10, '0b001111': 0b0110}
            fmt = '#0%db' % (highest + 2)
            return {format(mask, fmt): value for mask, value in masks.items()}
        else:
            # use ``into`` for rulename
            # like {'foo': 0b10, 'bar': 0b0110}
            return {into[mask]: value for mask, value in masks.items()}

    def validate(self, value=INVALID):
        """ checks if a match the rule set.

        value: will be checked against the ruleset. Default is ``self._valid``.
        returns:
        (valid value, rule name) for discrete and range rules.
        {mask: (valid val, rule name, mask_height, mask_width), ...} for binary masks rules.
        (INVALID, 'Invalid') if no matching is found.
        (value, 'Default') if rule set is empty.
        Parameters
        ----------

        Returns
        -------
        """

        if value is INVALID:
            value = self._value

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
                        vtest, mask_height, mask_width = masked(value, mask)
                        if vtest == vld:
                            # record, indexed by mask
                            binmasks[mask] += [vld, name,
                                               mask_height, mask_width]
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

    def toString(self, level=0, alist=False, **kwds):

        ret = exprstrs(self, level=level, **kwds)
        if alist:
            return ret
        vs, us, ts, ds, fs, gs, cs, ext = ret
        if level > 1:
            return '(%s: %s <%s>)' % (ts, vs, us)
        return '%s(%s: %s <%s>, "%s", default= %s, valid= %s tcode=%s)' % \
            (self.__class__.__name__, ts, vs, us, ds, fs, gs, cs)

    string = toString

    __str__ = toString

    def __getstate__(self):
        """ Can be encoded with serializableEncoder.
        Parameters
        ----------

        Returns
        -------
        """
        return OrderedDict(description=self.description,
                           type=self._type,
                           default=self._default,
                           value=self._value,  # must go behind type. maybe default
                           valid=self._valid,
                           listeners=self.listeners
                           )


MetaHeaders = ['name', 'value', 'unit', 'type', 'valid',
               'default', 'code', 'description']
ExtraAttributes = ['fits_keyword', 'id_zh_cn',
                   'description_zh_cn', 'valid_zh_cn']


class MetaData(ParameterListener, Composite, Copyable, DatasetEventSender):
    """ A container of named Parameters. A MetaData object can
    have one or more parameters, each of them stored against a
    unique name. The order of adding parameters to this container
    is important, that is: the keySet() method will return a set of
    labels of the parameters in the sequence as they were added.
    Note that replacing a parameter with the same name,
    will keep the order. """

    Table_Widths = [
        {'name': 15, 'value': 18, 'unit': 6, 'type': 8,
         'valid': 17, 'default': 15, 'code': 4, 'description': 17}
    ]

    def __init__(self, copy=None, defaults=None, **kwds):
        """

        Parameters
        ----------

        Returns
        -------
        """

        super().__init__(**kwds)
        if copy:
            # not implemented ref https://stackoverflow.com/questions/10640642/is-there-a-decent-way-of-creating-a-copy-constructor-in-python
            raise ValueError('use copy.copy() insteadof MetaData(copy)')
        else:
            self._defaults = [] if defaults is None else defaults
            return

    def accept(self, visitor):
        """ Hook for adding functionality to meta data object
        through visitor pattern.
        Parameters
        ----------

        Returns
        -------
        """
        visitor.visit(self)

    def clear(self):
        """ Removes all the key - parameter mappings.
        Parameters
        ----------

        Returns
        -------
        """
        self.getDataWrappers().clear()

    def set(self, name, newParameter):
        """ Saves the parameter and  adds eventhandling.

        In a parameter name, dot or other invalid characters (when the name is used as a property name) is ignored.

        Raises TypeError if not given Parameter (sub) class object.

        Parameters
        ----------

        Returns
        -------
        """
        if not issubclass(newParameter.__class__, AbstractParameter):
            if name == 'listeners' and issubclass(newParameter.__class__, list):
                pass
            elif name == '_STID' and issubclass(newParameter.__class__, str):
                pass
            else:
                raise TypeError('Only Parameters can be saved. %s is a %s.' %
                                (name, newParameter.__class__.__name__))

        super(MetaData, self).set(name, newParameter)

        if 'listeners' in self.__dict__:
            so, ta, ty, ch, ca, ro = self, self, -1,
            (name, newParameter), None, None
            if name in self.keySet():
                ty = EventType.PARAMETER_CHANGED
            else:
                ty = EventType.PARAMETER_ADDED
            e = DatasetEvent(source=so, target=ta, typ_=ty,
                             change=ch, cause=ca, rootCause=ro)
            self.fire(e)

    def __repr__(self):

        # return ydump(self.__getstate__(), default_flow_style=True)
        return self.toString(level=3)

    def remove(self, name):
        """ add eventhandling
        Parameters
        ----------

        Returns
        -------
        """
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

    def toString(self, level=0,
                 tablefmt='grid', tablefmt1='simple', tablefmt2='rst',
                 extra=False, param_widths=None, width=0, **kwds):
        """ return  string representation of metada.

        level: 0 is the most detailed, 2 is the least,
        tablefmt: format string in packae ``tabulate``, for level==0, tablefmt1 for level1, tablefmt2: format of 2D table data.
        param_widths: controls how the attributes of every parameter are displayed in the table cells. If is set to -1, there is no cell-width limit. For finer control set a dictionary of parameter attitute names and how many characters wide its tsble cell is, 0 for ommiting the attributable. Default is `MetaData.Table_Widths[0]`. e.g.
``{'name': 8, 'value': 17, 'unit': 7, 'type': 8,
                      'valid': 20, 'default': 17, 'code': 4, 'description': 15}``
        """

        if param_widths is None or param_widths == 0:
            param_widths = MetaData.Table_Widths[0]
        tab = []
        # N parameters per row for level 1
        N = 3
        i, row = 0, []
        cn = self.__class__.__name__
        s = ''
        att, ext = {}, {}
        has_omission = False
        nn = 0
        for (k, v) in self.__getstate__().items():
            if k.startswith('_ATTR_'):
                k = k[6:]
            elif k == '_STID':
                continue
            att['name'] = k
            # get values of line k.
            if issubclass(v.__class__, Parameter):
                att['value'], att['unit'], att['type'], att['description'],\
                    att['default'], att['valid'], att['code'], ext = v.toString(
                        level=level, width=0 if level > 1 else 1,
                        tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                        extra=extra,
                        alist=True)
                from ..utils.fits_kw import getFitsKw
                # make sure every line has fits_keyword in ext #1
                fk = ext.pop('fits_keyword') if 'fits_keyword' \
                    in ext else getFitsKw(k)
                ext0 = ext
                ext = {'fits_keyword': fk}
                ext.update(ext0)
            else:
                # listeners
                lstr = '' if v is None else v.toString(level=level, alist=True)
                if len(lstr) < 3:
                    lstr = [["", "<No listener>", ""]]
                att['value'], att['unit'], att['type'], att['description'] = \
                    '\n'.join(str(x[1]) for x in lstr), '', \
                    '\n'.join(x[0] for x in lstr), \
                    '\n'.join(x[2] for x in lstr)
                att['default'], att['valid'], att['code'] = '', '', ''
                ext = dict((n, '') for n in ext)

            # generate column vallues of the line and ext headers
            # limit cell width for level=0,1.
            if level == 0:
                if param_widths == -1:
                    l = tuple(att[n] for n in MetaHeaders)
                    if extra:
                        l += tuple(v for v in ext.values())
                else:
                    l = tuple(
                        wls(att[n], w)
                        for n, w in param_widths.items() if w != 0)
                    if extra:
                        l += tuple(
                            wls(v, Default_Extra_Param_Width)
                            for v in ext.values())
                        # print(l)

                tab.append(l)
                exh = [v for v in ext.keys()]

            elif level == 1:
                ps = '%s= %s' % (att['name'], att['value'])
                tab.append(wls(ps, 80//N))
                # s += mstr(self, level=level, tablefmt = tablefmt, \
                # tablefmt=tablefmt, tablefmt1=tablefmt1, \
                # tablefmt2=tablefmt2,depth=1, **kwds)
                if 0:
                    row.append(wls(ps, 80//N))
                    i += 1
                    if i == N:
                        tab.append(row)
                        i, row = 0, []
            else:
                n = att['name']
                if n in self._defaults and self._defaults[n]['default'] == v.value:

                    has_omission = True
                    pass
                elif n == 'listeners' and len(v) == 0:
                    has_omission = True
                else:
                    ps = '%s=%s' % (n, v.toString(level)) if level == 2 else n
                    # tab.append(wls(ps, 80//N))
                    tab.append(ps)
            #nn += 1
            # if nn == 2:
            #    pass  # break

        if has_omission:
            tab.append('..')

        # write out the table
        if level == 0:
            allh = (MetaHeaders + exh) if extra else MetaHeaders
            if param_widths == -1:
                headers = allh
            else:
                headers = []
                for n in allh:
                    w = param_widths.get(n, Default_Extra_Param_Width)
                    #print(n, w)
                    if w != 0:
                        headers.append(wls(n, w))
            fmt = tablefmt
            s += tabulate.tabulate(tab, headers=headers, tablefmt=fmt, missingval='',
                                   disable_numparse=True)
        elif level == 1:
            t = grouper(tab, N)
            headers = ''
            fmt = tablefmt1
            s += tabulate.tabulate(t, headers=headers, tablefmt=fmt, missingval='',
                                   disable_numparse=True)
        elif level > 1:  # level 2 and 3
            s = ', '.join(tab) if len(tab) else 'Default Meta'
            l = '.'
            return '<' + self.__class__.__name__ + ' ' + s + l + '>'

        return '\n%s' % (s) if len(tab) else '(No Parameter.)'

        # return '\n%s\n%s-listeners = %s' % (s, cn, lsnr) if len(tab) else \
        #    '%s %s-listeners = %s' % ('(No Parameter.)', cn, lsnr)

    string = toString

    def __getstate__(self):
        """ Can be encoded with serializableEncoder
        Parameters
        ----------

        Returns
        -------
        """

        # print(self.listeners)
        # print([id(o) for o in self.listeners])

        return OrderedDict(**self.data,
                           _ATTR_listeners=self.listeners)
