# -*- coding: utf-8 -*-

# Automatically generated from fdi/dataset/resources/BaseProduct.yml. Do not edit.

from collections import OrderedDict
from fdi.dataset.finetime import FineTime


from .serializable import Serializable
from .abstractcomposite import AbstractComposite
from .listener import EventSender, EventType
from .metadata import AbstractParameter, Parameter, NumericParameter, ParameterTypes, StringParameter, DateParameter
from .eq import deepcmp
from .copyable import Copyable
from .history import History

import pdb

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


# @addMandatoryProductAttrs


class BaseProduct( AbstractComposite, Copyable, Serializable,  EventSender):
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

    BaseProduct class (level ALL) schema 1.1 inheriting [None]. Automatically generated from fdi/dataset/resources/BaseProduct.yml on 2020-09-13 17:02:23.295850.

    """


    def __init__(self,
                 description = 'UNKNOWN',
                 type_ = 'BaseProduct',
                 creator = 'UNKNOWN',
                 creationDate = FineTime(0),
                 rootCause = 'UNKNOWN',
                 version = '0.6',
                 **kwds):

        global ProductInfo
        self.pInfo = ProductInfo

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

        # print(self.pInfo['metadata'].keys())
        # print(metasToBeInstalled)
        # print('# ' + self.meta.toString(level=0))

        self.installMetas(mtbi=metasToBeInstalled)
        self.history = History()

    def installMetas(self, mtbi, prodInfo=None):
        """ put parameters in group in product metadata, and updates productInfo. values in mtbi override those default ones in group.
        """
        if prodInfo is None:
            prodInfo = self.pInfo

        for met, params in prodInfo['metadata'].items():
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
        if name not in ['pInfo', '_meta'] and hasattr(self, '_meta'):
            #            self.hasMeta():
            if name in self.pInfo['metadata']:
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
            met = self.pInfo['metadata']
            if name in met.keys():
                # a built-in attribute like 'description'. store in meta
                m = self.getMeta()
                if name in m:
                    # meta already has a Parameter for name
                    p = m[name]
                    if issubclass(value.__class__, AbstractParameter):
                        t, tt = value.getType(), p.getType()
                        if issubclass(t, tt):
                            p = value
                            return
                        else:
                            vs = value.value
                            raise TypeError(
                                "Parameter %s type is %s, not %s's %s." % (vs, t, name, tt))
                    else:
                        # value is not a Parameter
                        t_type = type(value)
                        tt_type = type(p.value)
                        if issubclass(t_type, tt_type):
                            p.setValue(value)
                            return
                        else:
                            vs = value
                            raise TypeError(
                                "Value %s type is %s, not %s's %s." % (vs, t_type.__name__, name, tt_type.__name__))
                else:
                    # name is not in prod metadata.

                    if issubclass(value.__class__, AbstractParameter):
                        # value is a parameter
                        m[name] = value
                        return
                    # value is not  a Parameter make one.
                    m[name] = value2parameter(name, value, met)
                # must return without updating self.__dict__
                return
        # print('setattr ' + name, value)
        super(BaseProduct, self).__setattr__(name, value)

    def __delattr__(self, name):
        """ Refuses deletion of mandatory attributes
        """
        if name in self.pInfo['metadata'].keys():
            logger.warn('Cannot delete Mandatory Attribute ' + name)

        super(BaseProduct, self).__delattr__(name)

    def setMeta(self, newMetadata):
        super(BaseProduct, self).setMeta(newMetadata)
        # self.getMeta().addListener(self)

    def targetChanged(self, event):
        pass
        if event.source == self.meta:
            if event.type_ == EventType.PARAMETER_ADDED or \
               event.type_ == EventType.PARAMETER_CHANGED:
                # logger.debug(event.source.__class__.__name__ +   ' ' + str(event.change))
                pass

    def toString(self, matprint=None, trans=True, beforedata='', level=0):
        """ like AbstractComposite but with history
        """
        h = self.history.toString(matprint=matprint, trans=trans, level=level)
        s = super(BaseProduct, self).toString(
            matprint=matprint, trans=trans, beforedata=h, level=level)
        return s

    def __repr__(self):
        ''' meta and datasets only show names
        '''
        s = '{'
        """for lvar in self.pInfo['metadata'].keys():
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
        if 0:
            # remove self from meta's listeners because the deserialzed product will add itself during instanciation.
            print('1###' + self.meta.toString())
            metac = self.meta.copy()
            print('***' + metac.toString())
            print(deepcmp(self, metac.listeners[0]))
            metac.removeListener(self)

        ls = [
            ("meta", self.meta),
            ("_sets", self._sets),
            ("history", self.history),
            ("listeners", self.listeners),
            ("classID", self.classID)]

        return OrderedDict(ls)


def value2parameter(name, value, met):
    """ returns a parameter with correct type and attributes according to its value and name.

    met is pInfo('metadata'] or pInfo['dataset'][xxx]
    """
    
    im = met[name]  # {'dats_type':..., 'value':....}
    # in ['integer','hex','float','vector','quaternion']
    if 'unit' in im and im['unit'] is not None:
        ret = NumericParameter(value=value,
                                   description=im['description'],
                                   typ_=im['data_type'],
                                   unit=im['unit'],
                                   default=im['default'],
                                   valid=im['valid'],
                                   typecode=im['typecode'],
 						   )
    elif im['data_type'] == 'string':
        fs = im['default'] if 'default' in im else None
        gs = im['valid'] if 'valid' in im else None
        cs = im['typecode'] if 'typecode' in im else 'B'
        ret = StringParameter(value=value,
                            description=im['description'],
                            default=fs,
                            valid=gs,
                            typecode=cs
                            )
    elif im['data_type'] == 'finetime':
        fs = im['default'] if 'default' in im else None
        gs = im['valid'] if 'valid' in im else None
        cs = im['typecode'] if 'typecode' in im else None
        ret = DateParameter(value=value,
                            description=im['description'],
                            default=fs,
                            valid=gs,
                            typecode=cs
                            )
    else:
        fs = im['default'] if 'default' in im else None
        gs = im['valid'] if 'valid' in im else None
        ret = Parameter(value=value,
                            description=im['description'],
                            typ_=im['data_type'],
                            default=fs,
                            valid=gs,
                            )
    return ret
 
def addMandatoryProductAttrs(cls):
    """mh: Add MPAs to a class so that although they are metadata,
    they can be accessed by for example, productfoo.creator.
    dynamic properties see
    https://stackoverflow.com/a/2584050
    https://stackoverflow.com/a/1355444
    """
    for name in self.pInfo['metadata'].keys():
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

ProductInfo = {
    'name': 'BaseProduct',
    'description': 'FDI base class',
    'parents': [
        None,
        ],
    'level': 'ALL',
    'schema': '1.1',
    'metadata': {
        'description': {
                'current_id': 'description',
                'id': 'description',
                'id_zh_cn': '描述',
                'fits_keyword': 'DESCRIPT',
                'data_type': 'string',
                'description': 'Description of this product',
                'description_zh_cn': '对本产品的描述。',
                'examples': 'SINGLE EXPOSURE',
                'default': 'UNKNOWN',
                'valid': '',
                'typecode': 'B',
                },
        'type': {
                'current_id': 'type',
                'id': 'type',
                'id_zh_cn': '产品类型',
                'fits_keyword': 'TYPE',
                'data_type': 'string',
                'description': 'Product Type identification. Name of class or CARD.',
                'description_zh_cn': '产品类型。完整Python类名或卡片名。',
                'examples': 'SAT-QM-ThermVac',
                'default': 'BaseProduct',
                'valid': '',
                'typecode': 'B',
                },
        'creator': {
                'current_id': 'creator',
                'id': 'creator',
                'id_zh_cn': '本产品生成者',
                'fits_keyword': 'CREATOR',
                'data_type': 'string',
                'description': 'Generator of this product.',
                'description_zh_cn': '本产品生成方的标识，例如可以是单位、组织、姓名、软件、或特别算法等。',
                'examples': 'SECM-EGSE',
                'default': 'UNKNOWN',
                'valid': '',
                'typecode': 'B',
                },
        'creationDate': {
                'current_id': 'creationDate',
                'id': 'creationDate',
                'id_zh_cn': '产品生成时间',
                'fits_keyword': 'DATE',
                'data_type': 'finetime',
                'description': 'Creation date of this product',
                'description_zh_cn': '本产品生成时间',
                'examples': '10361455509632',
                'default': 0,
                'valid': '',
                'typecode': None,
                },
        'rootCause': {
                'current_id': 'rootCause',
                'id': 'rootCause',
                'id_zh_cn': '数据来源',
                'fits_keyword': 'ROOTCAUS',
                'data_type': 'string',
                'description': 'Reason of this run of pipeline.',
                'description_zh_cn': '数据来源（此例来自鉴定件热真空罐）',
                'examples': 'QM-ThermVac',
                'default': 'UNKNOWN',
                'valid': '',
                'typecode': 'B',
                },
        'version': {
                'current_id': 'formatVersion',
                'id': 'version',
                'id_zh_cn': '格式版本',
                'fits_keyword': 'VERSION',
                'data_type': 'string',
                'description': 'Version of product schema',
                'description_zh_cn': '产品格式版本',
                'examples': '1',
                'default': '0.6',
                'valid': '',
                'typecode': 'B',
                },
        },
    'datasets': {
        },
    }

