# -*- coding: utf-8 -*-

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
from .finetime import FineTime, FineTime1, utcobj
from .odict import ODict
from .serializable import Serializable


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
        super(History, self).__init__(**kwds)

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
        super(Product, self).__init__(**kwds)

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
        return super(Product, self).__getattribute__(name)

    def setMeta(self, newMetadata):
        super(Product, self).setMeta(newMetadata)
        self.getMeta().addListener(self)

    def __setattr__(self, name, value, withmeta=True):
        """ Updates meta data table when Mandatory Attributes are
        modifed
        """
        if name in mandatoryProductAttrs and withmeta:
            self.getMeta()[name] = value
        else:
            #print('setattr ' + name, value)
            super(Product, self).__setattr__(name, value)

    def __delattr__(self, name):
        """ Refuses deletion of mandatory attributes
        """
        if name in mandatoryProductAttrs:
            logger.warn('Cannot delete Mandatory Attribute ' + name)
            return

        super(Product, self).__delattr__(name)

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
        s = super(Product, self).toString(
            matprint=matprint, trans=trans, beforedata=h)
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
            ("listeners", self.listeners),
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
