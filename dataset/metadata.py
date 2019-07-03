import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

from dataset.annotatable import Annotatable
from dataset.copyable import Copyable
from dataset.eq import DeepEqual
from dataset.listener import EventSender, DatasetBaseListener, ParameterListener, DatasetListener, DatasetEvent, EventType
from dataset.composite import Composite
from dataset.odict import ODict
from dataset.serializable import Serializable


class Parameter(Annotatable, Copyable, DeepEqual, EventSender, Serializable):
    """ Parameter is the interface for all named attributes
    in the MetaData container. It can have a value and a description."""

    def __init__(self, value=None, **kwds):
        """ invoked with no argument results in a parameter of
        None value and 'UNKNOWN' description.
        With a signle argument: arg -> value, 'UNKNOWN'-> description.
        With two positional arguments: arg1 -> value, arg2-> description.
        """
        super().__init__(**kwds)
        self.value = value
        self.type = value.__class__.__name__

    def accept(self, visitor):
        """ Adds functionality to classes of this type."""
        visitor.visit(self)

    def getType(self):
        """ Returns the actual type that is allowed for the value
        of this Parameter."""
        return self.value.__class__.__name__

    def getValue(self):
        """ Gets the value of this parameter as an Object. """
        return self.value

    def setValue(self, newValue):
        """ Replaces the current value of this parameter. """
        self.value = newValue

    def __setattr__(self, name, value):
        """ add eventhandling """
        super().__setattr__(name, value)

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
            e = DatasetEvent(source=so, target=ta, type=ty,
                             change=ch, cause=ca, rootCause=ro)
            self.fire(e)

    def __set1__(self, obj, type):
        print('s ' + name + str(type))
        self.__setattr__(name, value)

    def __get1__(self, name):
        print('g ' + name)
        self.__getattr__(name)

    def __delete1__(self, name):
        print('d ' + name)
        self.__delattr__(name)

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
                     type=self.type,
                     classID=self.classID,
                     version=self.version)


class Quantifiable():
    """ A Quantifiable object is a numeric object that has a unit.
    $ x.unit = ELECTRON_VOLTS
    $ print x.unit
    eV [1.60218E-19 J]"""

    def __init__(self, unit=None, **kwds):
        """

        """
        self.unit = unit
        super().__init__(**kwds)

    def getUnit(self):
        """ Returns the unit related to this object."""
        return self.unit

    def setUnit(self, unit):
        """ Sets the unit of this object. """
        self.unit = unit


class NumericParameter(Parameter, Quantifiable):
    """
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
                     type=self.type,
                     classID=self.classID,
                     version=self.version)


class MetaData(Composite, Copyable, Serializable, ParameterListener, EventSender):
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
            e = DatasetEvent(source=so, target=ta, type=ty,
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
            e = DatasetEvent(source=so, target=ta, type=ty,
                             change=ch, cause=ca, rootCause=ro)
            self.fire(e)
        return r

    def toString(self):
        s, l = '', ''
        for (k, v) in self.sets.items():
            s = s + str(k) + ' = ' + str(v) + ', '
        l = ''.join(['"' + x.description + '", ' for x in self.listeners])
        return self.__class__.__name__ + \
            '{[' + s + '], listeners = [%s]}' % (l)

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(sets=self.sets,
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


class Mk():

    def __init__(self, **kwds):
        print('mk')


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


class DataWrapper(Annotatable, Quantifiable, Copyable, DeepEqual):
    """ A DataWrapper is a composite of data, unit and description.
    mh: note that all data are in the same unit. There is no metadata.
    Implemented from AbstractDataWrapper.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.data = None

    def getData(self):
        """ Returns the data in this """
        return self.data

    def getUnit(self):
        """ Returns the unit related to this object. """
        return self.unit

    def hasData(self):
        """ Returns whether this data wrapper has data. """
        return self.data is not None

    def setData(self, data):
        """ Populates this DataWrapper with actual data. """
        self.data = data

    def setUnit(self, unit):
        """ Sets the unit of this object.. """
        self.unit = unit

    def __repr__(self):
        return self.__class__.__name__ + \
            '{ description = "%s", data = "%s", unit = "%s"}' % \
            (str(self.description), str(self.data), str(self.unit))


class DataWrapperMapper():
    """ Object holding a map of data wrappers. """

    def getDataWrappers(self):
        """ Gives the data wrappers, mapped by name. """
        return self.sets


class AbstractComposite(Attributable, Annotatable, Composite, DataWrapperMapper, DatasetListener):
    """ an annotatable and attributable subclass of Composite. 
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def __repr__(self):
        ''' meta and datasets only show names
        '''
        s = '{'
        s += 'meta = "%s", sets = %s}' % (
            str(self.meta),
            str(self.keySet())
        )
        return s

    def toString(self):
        s = '{'
        s += 'meta = %s, sets = %s}' % (
            self.meta.toString(),
            self.sets.__str__()
        )
        return s
