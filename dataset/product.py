# -*- coding: utf-8 -*-
from collections import OrderedDict
import datetime
import pprint

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .copyable import Copyable
from .eq import DeepEqual
# from .composite import
from .dataset import CompositeDataset
from .listener import EventSender, DatasetEvent, DatasetListener, EventType
from .abstractcomposite import AbstractComposite
from .odict import ODict
from .serializable import Serializable


class FineTime1(Copyable, DeepEqual, Serializable):
    """ Atomic time(SI seconds) elapsed since the TAI epoch
    of 1 January 2000 UT2. The resolution is one microsecond and the
    allowable range is: epoch + /-290, 000 years approximately.

    This has the following advantages, compared with the standard class:

    It has better resolution(microseconds)
    Time differences are correct across leap seconds
    It is immutable
    """

    EPOCH = datetime.datetime(2000, 1, 1, 0, 0, 0,
                              tzinfo=datetime.timezone.utc)  # posix timestamp

    def __init__(self, date=None, **kwds):
        """ Initiate with a UTC date """
        leapsec = 0  # leap seconds to be implemented
        if date is None:
            self.tai = int(0)
        else:
            if date.tzinfo is None:
                d = date.replace(tzinfo=datetime.timezone.utc)
            else:
                d = date
            self.tai = int(1000000) * \
                ((d - FineTime1.EPOCH).total_seconds() + leapsec)
        # logger.debug('date= %s TAI = %d' % (str(date), self.tai))
        super().__init__(**kwds)

    def microsecondsSinceEPOCH(self):
        """ Return the number of microseconds since the epoch: 1 Jan 1958. """
        return tai

    def subtract(self, time):
        """ Subract the specified time and return the difference
        in microseconds. """
        return self.tai - time.tai

    def toDate(self):
        """ Return this time as a Python Date. """
        leapsec = 0  # leap seconds to be implemented
        return datetime.timedelta(seconds=(self.tai / 1000000. - leapsec))\
            + FineTime1.EPOCH

    def toString(self):
        """ Returns a String representation of this object.
        prints like 2019 - 02 - 17T12: 43: 04.577000 TAI """
        dt = datetime.timedelta(
            seconds=(self.tai / 1000000.)) + FineTime1.EPOCH
        # return dt.isoformat(timespec='microseconds')
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f TAI') +\
            '(%d)' % (self.tai)

    def __repr__(self):
        return self.toString()

    def __str__(self):
        return self.toString()

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(tai=self.tai,
                     classID=self.classID,
                     version=self.version)


class History(CompositeDataset, DeepEqual):
    """ Public interface to the history dataset. Contains the
    main methods for retrieving a script and copying the history.
    """

    def __init__(self, other=None, **kwds):
        """
        mh: The copy constructor is better not be implemented. Use copy()
        instead. Remember: not only copies the datasets,
        but also changes the history ID in the metadata and
        relevant table entries to indicate that this a new
        independent product of which the history may change.
        """
        super().__init__(**kwds)

        # Name of the table which contains the history script
        self.HIST_SCRIPT = ''
        # Name of the parameter history table
        self.PARAM_HISTORY = ''
        # Name of the task history table
        self.TASK_HISTORY = ''

    def accept(self, visitor):
        """ Hook for adding functionality to meta data object
        through visitor pattern."""
        visitor.visit(self)

    def getOutputVar(self):
        """ Returns the final output variable of the history script.
        """
        return None

    def getScript(self):
        """ Creates a Jython script from the history.
        """
        return self.HIST_SCRIPT

    def getTaskHistory(self):
        """ Returns a human readable formatted history tree.
        """
        return self.TASK_HISTORY

    def saveScript(self, file):
        """ Saves the history script to a file.
        """

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        return ODict(description=self.description,
                     HIST_SCRIPT=self.HIST_SCRIPT,
                     PARAM_HISTORY=self.PARAM_HISTORY,
                     TASK_HISTORY=self.TASK_HISTORY,
                     meta=self.meta,
                     _sets=self._sets,
                     classID=self.classID,
                     version=self.version)


mandatoryProductAttrs = ['description', 'creator', 'creationDate',
                         'instrument', 'startDate', 'endDate',
                         'rootCause',
                         'modelName', 'type', 'mission']


#@addMandatoryProductAttrs
class Product(AbstractComposite, Copyable, Serializable,  EventSender):
    """ A Product is a generic result that can be passed on between
    (standalone) processes.

    In general a Product contains zero or more datasets, history,
    optional metadata as well as some required metadata fields.
    Its intent is that it can fully describe itself; this includes
    the way how this product was achieved (its history). As it is
    the result of a process, it should be able to save to and restore
    from an Archive device.

    Many times a Product may contain a single dataset and for this
    purpose the first dataset entry can be accessed by the getDefault()
    method. Note that the datasets may be a composite of datasets
    by themselves.

    mh: Mandatory Attributes can be accessed with e.g. p.creator
    or p.meta['creator']
    """

    def __init__(self, creator='',
                 creationDate=None,
                 instrument='',
                 startDate='',
                 endDate='',
                 rootCause='UNKNOWN',
                 modelName='UNKNOWN',
                 type='UNKNOWN',
                 mission='SVOM',
                 **kwds):

        # must be the first line to initiate meta and get description
        super().__init__(**kwds)

        creationDate = FineTime1() if creationDate is None else creationDate
        # list of local variables. 'description' has been consumed in
        # in annotatable super class so it is not in.
        lvar = locals()
        lvar.pop('self')
        # print('# ' + self.meta.toString())
        # print(self.__dict__)
        for ma in mandatoryProductAttrs:
            # description has been set by Anotatable.__init__
            if ma != 'description':
                # metadata entries are also set by extended setattr
                self.__setattr__(ma, lvar[ma])

        #print('% ' + self.meta.toString())
        self.history = History()

    def accept(self, visitor):
        """ Hook for adding functionality to meta data object
        through visitor pattern."""
        visitor.visit(self)

    def getDefault(self):
        """ Convenience method that returns the first dataset \
        belonging to this product. """
        return list(self._sets.values())[0] if len(self._sets) > 0 else None

    def __getattribute__(self, name, withmeta=True):
        """ Reads meta data table when Mandatory Attributes are
        read
        """
        #print('getattribute ' + name)
        if name in mandatoryProductAttrs and withmeta:
            # if meta does not exist, inherit Attributable
            # before any class that access mandatory attributes
            #print('aa ' + str(self.getMeta()[name]))
            return self.getMeta()[name]
        return super().__getattribute__(name)

    def setMeta(self, newMetadata):
        super().setMeta(newMetadata)
        self.getMeta().addListener(self)

    def __setattr__(self, name, value, withmeta=True):
        """ Updates meta data table when Mandatory Attributes are
        modifed
        """
        if name in mandatoryProductAttrs and withmeta:
            self.getMeta()[name] = value
        else:
            #print('setattr ' + name, value)
            super().__setattr__(name, value)

    def __delattr__(self, name):
        """ Refuses deletion of mandatory attributes
        """
        if name in mandatoryProductAttrs:
            logger.warn('Cannot delete Mandatory Attribute ' + name)
            return

        super().__delattr__(name)

    def targetChanged(self, event):
        pass
        if event.source == self.meta:
            if event.type_ == EventType.PARAMETER_ADDED or \
               event.type_ == EventType.PARAMETER_CHANGED:
                #logger.debug(event.source.__class__.__name__ +   ' ' + str(event.change))
                pass

    def toString(self, matprint=None, trans=True, beforedata=''):
        """ like AbstractComposite but with history
        """
        h = self.history.toString(matprint=matprint, trans=trans)
        s = super().toString(matprint=matprint, trans=trans, beforedata=h)
        return s

    def __repr__(self):
        ''' meta and datasets only show names
        '''
        s = '{'
        """for lvar in mandatoryProductAttrs:
            if hasattr(self, lvar):
                s += '%s = %s, ' % (lvar, getattr(self, lvar))
        """
        s += 'meta = "%s", _sets = %s, history = %s}' % (
            str(self.meta),
            str(self.keySet()),
            str(self.history)
        )
        return s

    def serializable(self):
        """ Can be encoded with serializableEncoder """
        # remove self from meta's listeners because the deserialzed product will add itself during instanciation.
        metac = self.meta.copy()
        #print('***' + metac.toString())
        metac.removeListener(self)
        # ls = [(lvar, getattr(self, lvar)) for lvar in mandatoryProductAttrs]
        ls = [
            ("meta", metac),
            ("_sets", self._sets),
            ("history", self.history),
            ("listenersurn", self.listenersurn),
            ("classID", self.classID),
            ("version", self.version)]
        return ODict(ls)


def addMandatoryProductAttrs(cls):
    """mh: Add MPAs to a class so that although they are metadata,
    they can be accessed by for example, productfoo.creator.
    dynamic properties see
    https://stackoverflow.com/a/2584050
    https://stackoverflow.com/a/1355444
    """
    for name in mandatoryProductAttrs:
        def g(self):
            return self._meta[name]

        def s(self, value):
            self._meta[name] = value

        def d(self):
            logger.warn('Cannot delete Mandatory Product Attribute ' + name)

        setattr(cls,
                name,
                property(lambda self: self._meta[name],
                         lambda self, val: self._meta.set(name, val),
                         lambda self: logger.warn(
                    'Cannot delete Mandatory Product Attribute ' + name),
                    'Mandatory Product Attribute ' + name))
#        setattr(cls, name, property(
#            g, s, d, 'Mandatory Product Attribute '+ name))
    return cls


#Product = addMandatoryProductAttrs(Product)
