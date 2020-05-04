# -*- coding: utf-8 -*-

from .serializable import Serializable
from .odict import ODict
from .finetime import FineTime, FineTime1, utcobj
from .abstractcomposite import AbstractComposite
from .listener import EventSender, DatasetEvent, DatasetListener, EventType
from .dataset import CompositeDataset
from .metadata import Parameter, NumericParameter, ParameterTypes
from .eq import DeepEqual
from .copyable import Copyable

from collections import OrderedDict
import pdb

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


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


# @addMandatoryProductAttrs


class BaseProduct(AbstractComposite, Copyable, Serializable,  EventSender):
    """ A BaseProduct is a generic result that can be passed on between
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

    mh: Built-in Attributes in productInfo['metadata'] can be accessed with e.g. p.creator
    or p.meta['description'].value:
    p.creator='foo'
    assert p.creatur=='foo'
    assert p.meta['creator']=='foo'
    p.meta['creator']=Parameter('bar')
    assert p.meta['creator']==Parameter('bar')
    """
    productInfo = {
        'metadata': OrderedDict({
            'description': {
                'data_type': 'string',
                'description': 'Description of this product',
                'unit': 'None',
                'default': 'UNKOWN',
            },
            'type': {
                'data_type': 'string',
                'description': 'Product Type identification. Fully qualified Python class name or CARD.',
                'unit': 'None',
                'default': 'BaseProduct',
            },
            'creator': {
                'data_type': 'string',
                'description': 'Generator of this product. Example name of institute, organization, person, software, special algorithm etc.',
                'unit': 'None',
                'default': 'UNKOWN',
            },
            'creationDate': {
                'data_type': 'finetime',
                'description': 'Creation date of this product',
                'unit': '',
                'default': '0',
            },
            'rootCause': {
                'data_type': 'string',
                'description': 'Reason of this run of pipeline.',
                'unit': 'None',
                'default': 'UNKOWN',
            },
            'schema': {
                'data_type': 'string',
                'description': 'Version of product schema',
                'unit': 'None',
                'default': '0.3',
            },
        })
    }

    def __init__(self,
                 description='UNKOWN',
                 creator='UNKOWN',
                 creationDate=FineTime1(0),
                 rootCause='UNKOWN',
                 type_='BaseProduct',
                 schema='0.3',
                 **kwds):

        if 'metasToBeInstalled' not in kwds:
            # this class is being called directly

            # list of local variables.
            lvar = locals()
            lvar.pop('self')
            lvar.pop('__class__')
            lvar.pop('kwds')
            metasToBeInstalled = lvar
        else:
            # This class is being called probably from super() in a subclass
            metasToBeInstalled = kwds['metasToBeInstalled']
            del kwds['metasToBeInstalled']
        # 'description' is consumed in annotatable super class so it is not in.
        description = metasToBeInstalled.pop('description')
        # print('B')
        # print(metasToBeInstalled)
        # print(description)

        # must be the first line to initiate meta and get description
        super(BaseProduct, self).__init__(description=description, **kwds)

        # print(self.productInfo['metadata'].keys())
        # print(metasToBeInstalled)
        # print('# ' + self.meta.toString())

        self.installMetas(mtbi=metasToBeInstalled)
        self.history = History()

    def installMetas(self, mtbi):
        """ put parameters in group in product metadata, and updates productInfo. values in mtbi override those default ones in group.
        """

        for met, params in self.productInfo['metadata'].items():
            # pdb.set_trace()  # description has been set by Anotatable.__init__
            if met != 'description':
                #  type_ in mtbi (from __init__) changed to type
                name = 'type_' if met == 'type' else met
                # set to input if given or to default.
                if name in mtbi:
                    value = mtbi[name]
                    self.__setattr__(met, value)

    def accept(self, visitor):
        """ Hook for adding functionality to meta data object
        through visitor pattern."""
        visitor.visit(self)

    def getDefault(self):
        """ Convenience method that returns the first dataset \
        belonging to this product. """
        return list(self._sets.values())[0] if len(self._sets) > 0 else None

    def __getattribute__(self, name, withmeta=True):
        """ Returns the named metadata parameter. Reads meta data table when Mandatory Attributes are
        read, and returns the values only.
        """
        # print('getattribute ' + name)
        if name not in ['productInfo', '_meta'] and hasattr(self, '_meta'):
            #            self.hasMeta():
            if name in self.productInfo['metadata']:
                # if meta does not exist, inherit Attributable
                # before any class that access mandatory attributes
                # print('aa ' + selftr(self.getMeta()[name]))
                return self.getMeta()[name].getValue()
        return super(BaseProduct, self).__getattribute__(name)

    def __setattr__(self, name, value, withmeta=True):
        """ Stores value to attribute with name given. 
        If name is in the built-in list, store the value in a Parameter in metadata container. Updates meta data table. Updates value when built-in Attributes already has its Parameter in metadata.
        value: Must be Parameter/NumericParameter if this is normal metadata, depending on if it is Number. Value if mandatory / built-in attribute.
        """
        if self.hasMeta():
            met = self.productInfo['metadata']
            if name in met.keys():
                # a special attribute like 'description'. store in meta
                m = self.getMeta()
                if name in m:
                    # meta already has a Parameter for name
                    p = m[name]
                    if issubclass(value.__class__, Parameter):
                        t, tt = value.getType(), p.getType()
                        if t == tt:  # TODO: subclass
                            p = value
                            return
                        else:
                            vs = value.value
                            raise TypeError(
                                'Parameter %s type is %s, not %s.' % (vs, t, tt))
                    else:
                        # value is not a Parameter
                        t = type(value).__name__
                        tt = ParameterTypes[p.getType()]
                        if t == tt:  # TODO: subclass
                            p.setValue(value)
                            return
                        else:
                            vs = value
                            raise TypeError(
                                'Parameter %s type is %s, not %s.' % (vs, t, tt))
                else:
                    # name is not in prod metadata. make a Parameter
                    im = met[name]  # {'dats_type':..., 'value':....}
                    # in ['integer','hex','float','vector','quaternion']
                    if im['unit']:
                        m[name] = NumericParameter(value=value,
                                                   description=im['description'],
                                                   type_=im['data_type'],
                                                   unit=im['unit'])
                    else:
                        m[name] = Parameter(value=value,
                                            description=im['description'],
                                            type_=im['data_type'])
                # must return without updating self.__dict__
                return
        # print('setattr ' + name, value)
        super(BaseProduct, self).__setattr__(name, value)

    def __delattr__(self, name):
        """ Refuses deletion of mandatory attributes
        """
        if name in self.productInfo['metadata'].keys():
            logger.warn('Cannot delete Mandatory Attribute ' + name)

        super(BaseProduct, self).__delattr__(name)

    def setMeta(self, newMetadata):
        super(BaseProduct, self).setMeta(newMetadata)
        self.getMeta().addListener(self)

    def targetChanged(self, event):
        pass
        if event.source == self.meta:
            if event.type_ == EventType.PARAMETER_ADDED or \
               event.type_ == EventType.PARAMETER_CHANGED:
                # logger.debug(event.source.__class__.__name__ +   ' ' + str(event.change))
                pass

    def toString(self, matprint=None, trans=True, beforedata=''):
        """ like AbstractComposite but with history
        """
        h = self.history.toString(matprint=matprint, trans=trans)
        s = super(BaseProduct, self).toString(
            matprint=matprint, trans=trans, beforedata=h)
        return s

    def __repr__(self):
        ''' meta and datasets only show names
        '''
        s = '{'
        """for lvar in self.productInfo['metadata'].keys():
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
        # print('***' + metac.toString())
        metac.removeListener(self)
        # ls = [(lvar, getattr(self, lvar)) for lvar in self.productInfo['metadata'].keys()]
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
    for name in self.productInfo['metadata'].keys():
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


# Product = addMandatoryProductAttrs(Product)
