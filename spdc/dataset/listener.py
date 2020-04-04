# -*- coding: utf-8 -*-

from .serializable import Serializable
from .eq import DeepEqual
from ..pal.urn import Urn
from ..pal.common import getProductObject
from ..pns import common as psnc

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


#from dataset.metadata import Parameter

class EventListener(object):
    """ Generic interface for listeners that will listen to anything
    """

    def targetChanged(self,  *args, **kwargs):
        """ Informs that an event has happened in a target of 
        any type.
        """
        pass


class DatasetBaseListener(EventListener):
    """ Generic interface for listeners that will listen to events
    happening on a target of a specific type.
    Java Warning:
    The listener must be a class field in order to make an object
    hard reference.
    """

    def targetChanged(self, event):
        """ Informs that an event has happened in a target of the
        specified type."""
        pass


class ListnerSet(Serializable, DeepEqual, list):
    """ Mutable collection of Listeners of an EvenSender.
    """

    def __init__(self, **kwds):
        self._members = []
        super(ListnerSet, self).__init__(**kwds)

    @property
    def urns(self):
        return self.geturns()

    @urns.setter
    def urns(self, urns):
        self.seturns(urns)

    def seturns(self, urns):
        """ Replaces the current urn with specified argument. 
        """
        for urn in urns:
            try:
                l = ProductRef(urn).product
            except ValueError as e:
                logger.warn(str(e))
                continue
            self.addListener(l)

    def geturns(self, remove=None):
        """ Returns the current urns.
        """

        ret = [ProductRef(
            x).urn for x in self._members if remove is None or x != remove]

        return ret

    def equals(self, obj):
        """ compares with another one. """
        return True

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict()


class EventSender(object):
    """ adapted from Peter Thatcher's
    https://stackoverflow.com/questions/1092531/event-system-in-python/1096614#1096614
    """

    def __init__(self, **kwds):
        self._listeners = ListnerSet()
        super(EventSender, self).__init__(**kwds)

    @property
    def listeners(self):
        return self.getListeners()

    @listeners.setter
    def listeners(self, listeners):
        self.setListeners(listeners)

    def setListeners(self, listeners):
        """ Replaces the current Listeners with specified argument. 
        """
        self._listeners = ListnerSet()
        for listener in listeners:
            self.addListener(listener)

    def getListeners(self):
        """ Returns the current Listeners.
        """
        return self._listeners

    def addListener(self, listener, cls=EventListener):
        """ Adds a listener to this. """

        l = listener

        if issubclass(l.__class__, cls):
            if l not in self._listeners:
                self._listeners.append(l)
        else:
            raise TypeError(
                'Listener is not subclass of ' + str(cls) + ' .')
        return self

    def removeListener(self, listener):
        """ Removes a listener from this. """
        try:
            self._listeners.remove(listener)
        except:
            raise ValueError(
                "Listener das no listening registerd. Cannot remove.")
        return self

    def fire(self, *args, **kwargs):
        n = 0
        try:
            for listener in self._listeners:
                listener.targetChanged(*args, **kwargs)
                n += 1
        except Exception as e:
            logger.error('listener ' + str(n) +
                         ' got exception: ' + str(e) + ' ' + psnc.trbk(e))

    def getListenerCount(self):
        return len(self._listeners)

    __call__ = fire
    #__len__ = getHandlerCount


class DatasetEventSender(EventSender):
    def __init__(self, **kwds):
        super(DatasetEventSender, self).__init__(**kwds)

    def addListener(self, listener, cls=DatasetBaseListener):
        """ Adds a listener to this. """

        super(DatasetEventSender, self).addListener(listener, cls=cls)

        return self

    def fire(self, event):
        super(DatasetEventSender, self).fire(event)


class EventType(object):
    # A column has been added to the target TableDataset.
    COLUMN_ADDED = 0
    # A column has been changed in the target TableDataset.
    COLUMN_CHANGED = 1
    # A column has been removed from the target TableDataset.
    COLUMN_REMOVED = 2
    DATA_CHANGED = 3  # The targets data has changed.
    # A dataset has been added to the target composite.
    DATASET_ADDED = 4
    # A dataset has been changed in the target composite.
    DATASET_CHANGED = 5
    # A dataset has been removed from the target composite.
    DATASET_REMOVED = 6
    # The targets  has changed.
    DESCRIPTION_CHANGED = 7
    # The targets MetaData has been changed.
    METADATA_CHANGED = 8
    # A parameter has been added to the target meta data.
    PARAMETER_ADDED = 9
    # A parameter has been changed in the target meta data.
    PARAMETER_CHANGED = 10
    # A parameter has been removed from the target meta data.
    PARAMETER_REMOVED = 11
    # A row has been added to the target TableDataset.
    ROW_ADDED = 12
    # A row has been removed from the target TableDataset.
    ROW_REMOVED = 13
    # The targets unit has changed.
    UNIT_CHANGED = 14
    # Some value in the target object has changed.
    VALUE_CHANGED = 15


class DatasetEvent(Serializable):
    """
    """

    def __init__(self, source, target, type_, change, cause, rootCause, **kwds):
        # The object on which the Event initially occurred.
        self.source = source
        # the target of the event, which is the same object returned
        # by getSource, but strongly typed.
        if isinstance(target, source.__class__):
            self.target = target
        else:
            raise TypeError(str(target) + ' is not of type ' +
                            str(source.__class__))
        # the type of the event.
        self.type_ = type_
        # Gives more information about the change that caused the event.
        self.change = change
        # The underlying event that provoked this event,
        # or null if there is no finer cause.
        self.cause = cause
        # The first event in the chain that provoked this event,
        # or null if this event is its own root.
        self.rootCause = rootCause
        super(DatasetEvent, self).__init__(**kwds)

    def __eq__(self, o):
        """ """
        if not issubclass(o.__class__, self):
            return False
        return self.source == o.source and\
            self.target == o.target and \
            self.type_ == o.type_ and \
            self.change == o.change and \
            self.cause == o.cause and \
            self.rootCause == o.rootCause

    def __repr__(self):
        r = '{source=' + str(self.source) +\
            ', target=' + str(self.target) +\
            ', type_=' + str(self.type_) +\
            ', change=' + str(self.change) +\
            ', cause=' + str(self.cause) +\
            ', rootCause=' + str(self.rootCause) +\
            '}'
        return r

    def toString(self):
        return self.__repr__()

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        s = ODict(source=self.source,
                  target=self.target,
                  type_=self.type_,
                  change=self.change,
                  cause=self.cause,
                  rootCause=self.rootCause,
                  classID=self.classID,
                  version=self.version)
        return s


class ParameterListener(DatasetBaseListener):
    """ Listener for events occuring in a Parameter.
    Available types::

    * DESCRIPTION_CHANGED
    * UNIT_CHANGED
    * VALUE_CHANGED

    Cause is always null.

    Warning: The listener handler must be a class attribute in order to
    create an object hard reference. See DatasetBaseListener.
    """
    pass


class MetaDataListener(DatasetBaseListener):
    """ Listener for events occuring in MetaData.
    Available types::

    * PARAMETER_ADDED
    * PARAMETER_REMOVED
    * PARAMETER_CHANGED

    Possible causes:
    not null (for PARAMETER_CHANGED, if parameter internally changed)
    null (for PARAMETER_CHANGED, when set is called with a previous
    existing parameter, and rest)

    Warning: The listener handler must be a class attribute in order to
    create an object hard reference. See DatasetBaseListener.
    """


class DatasetListener(DatasetBaseListener):
    """ Listener for events occuring in MetaData.
    Available types::

    * DESCRIPTION_CHANGED, METADATA_CHANGED (all datasets)
    * DATA_CHANGED, UNIT_CHANGED (ArrayDataset)
    * COLUMN_ADDED, COLUMN_REMOVED, COLUMN_CHANGED, ROW_ADDED, VALUE_CHANGED (TableDataset)
    * DATASET_ADDED, DATASET_REMOVED, DATASET_CHANGED (CompositeDataset)

    Possible causes::

    * not null (METADATA_CHANGED, COLUMN_CHANGED, DATASET_CHANGED)
    * null (rest)

    Warning: The listener handler must be a class attribute in order to
    create an object hard reference. See DatasetBaseListener.
    """


class ColumnListener(DatasetBaseListener):
    """ Listener for events occuring in a Column.

    Available types::

    * DESCRIPTION_CHANGED
    * UNIT_CHANGED
    * DATA_CHANGED

    Cause is always null.
    """


class ProductListener(DatasetBaseListener):
    """ Listener for events occuring in Product.
    Available types::

    * METADATA_CHANGED
    * DATASET_ADDED
    * DATASET_REMOVED
    * DATASET_CHANGED

    Possible causes::

    * not null (METADATA_CHANGED, DATASET_CHANGED)
    * null (METADATA_CHANGED, DATASET_REMOVED, DATASET_CHANGED)

    Warning: The listener handler must be a class attribute in order to
    create an object hard reference. See DatasetBaseListener.
    """
