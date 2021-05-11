# -*- coding: utf-8 -*-
from .metadataholder import MetaDataHolder
from .metadata import AbstractParameter, Parameter, NumericParameter, StringParameter, DateParameter
from .datatypes import DataTypes

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

MdpInfo = {}


def addMetaDataProperty(cls):
    """mh: Add MDP to a class so that although they are metadata,
    they can be accessed by for example, productfoo.creator.

    dynamic properties see
    https://stackoverflow.com/a/2584050
    https://stackoverflow.com/a/1355444
    """
    # MdpInfo is evaluated at class import time
    for name in MdpInfo:
        def g(self, n=name):
            return self._meta[name].getValue()

        def s(self, value, n=name):
            self.setMDP(n, value, MdpInfo)

        def d(self, n=name):
            logger.warn('Cannot delete MetaData Property ' + n)
        setattr(cls, name, property(
            g, s, d, 'MetaData Property ' + name))
    return cls


class Attributable(MetaDataHolder):
    """ An Attributable object is an object that has the
    notion of meta data.

    MetaData Porperties (MDPs) are Attributes that store their properties in te metadata table.
    """

    def __init__(self, meta=None, zInfo=None, **kwds):
        """ Pick out arguments listed in MdpInfo then put get updated MdpInfo into MetaData meta.

        """
        self.zInfo = zInfo if zInfo else {'metadata': {}}
        # the list of arg names of the 'and' set
        # andset = set(MdpInfo) & set(kwds)
        mdps = dict((x, kwds.pop('typ_' if x == 'type' else x))
                    for x in self.zInfo['metadata'])
        super(Attributable, self).__init__(meta=meta, **kwds)
        self.setParameters(mdps)

    def setParameters(self, params):
        """ Set a group of name-value pairs to MetaData.

        params: a dictionary of name:value where value is a subclass of 
        `AbstractParameter`. value can be the value of a registerws MDP.
        ``type`` will be used if ``typ_`` is given as the name.
        """

        for met, value in params.items():
            #  typ_ in params (from __init__) changed to type
            name = 'type' if met == 'typ_' else met
            # set to input if given or to default.
            self.__setattr__(name, value)
            #print('@@@@', name, value)

    @property
    def meta(self):
        return self.getMeta()

    @meta.setter
    def meta(self, newMetadata):
        self.setMeta(newMetadata)

    def setMeta(self, newMetadata):
        """ Replaces the current MetaData with specified argument. 

        mh: Product will override this to add listener when meta is
        replaced
        """
        self._meta = newMetadata

    def __getattribute__(self, name):
        """ Returns the named metadata parameter. 

        Reads meta data table when Attributes are
        read, and returns the values only.
        """
        # print('getattribute ' + name)

        # print('aa ' + selftr(self.getMeta()[name]))

        if name != 'zInfo':
            try:
                if name in self.zInfo['metadata']:
                    return self._meta[name].getValue()
            except AttributeError:
                pass

        return super(Attributable, self).__getattribute__(name)

    def setMDP(self, name, value, met):
        m = self.getMeta()
        #print('MDP ', name, value, id(m), len(m))
        if name in m:
            # meta already has a Parameter for name
            p = m[name]
            if issubclass(value.__class__, AbstractParameter):
                tv, tp = value.getType(), p.getType()
                if issubclass(tv, tp):
                    p = value
                    return
                else:
                    vs = value.value
                    raise TypeError(
                        "Parameter %s type is %s, not %s's %s." % (vs, tv, name, tp))
            else:
                # value is not a Parameter
                v_type = type(value)
                p_type = type(p.value)
                if issubclass(v_type, p_type):
                    p.setValue(value)
                    return
                else:
                    vs = value
                    raise TypeError(
                        "Value %s type is %s, not %s's %s." % (vs, v_type.__name__, name, p_type.__name__))
        else:
            # named parameter is not in zInfo

            if issubclass(value.__class__, AbstractParameter):
                # value is a parameter
                m[name] = value
                return
            # value is not  a Parameter make one.
            m[name] = value2parameter(name, value, met)
        return

    def __setattr__(self, name, value):
        """ Stores value to attribute with name given.

        If name is in the `zInfo` list, store the value in a Parameter in 
        metadata container. Updates meta data table. Updates value when 
        an MDP attribute already has its Parameter in metadata.

        value: Must be Parameter/NumericParameter if this is normal metadata, 
        depending on if it is `Number`. `Value` is the value if the  attribute
        is an MDP
        """
        # print('setattr ' + name, value)
        try:
            met = self.zInfo['metadata']
            if name in met:
                # an MDP attribute like 'description'. store in meta
                self.setMDP(name, value, met)
                # must return without updating self.__dict__
                return
        except AttributeError:
            pass

        super(Attributable, self).__setattr__(name, value)

    def __delattr__(self, name):
        """ Refuses deletion of mandatory attributes.
        """

        try:
            if name in self.zInfo:
                logger.warn('Cannot delete MetaData Property ' + name)
                return
        except AttributeError:
            pass

        super(Attributable, self).__delattr__(name)


def value2parameter(name, value, descriptor):
    """ returns a parameter with correct type and attributes according to its value and name.

    value: type must be compatible with data_type. For example [0, 0] is wrong; Vector2d([0, 0)] is right if ``data_type``==``vector2d``.
    descriptor: is zInfo('metadata'] or zInfo['dataset'][xxx]
    """

    im = descriptor[name]  # {'dats_type':..., 'value':....}
    # in ['integer','hex','float','vector','quaternion']

    fs = im['default'] if 'default' in im else None
    gs = im['valid'] if 'valid' in im else None
    if im['data_type'] == 'string':
        cs = im['typecode'] if 'typecode' in im else 'B'
        ret = StringParameter(value=value,
                              description=im['description'],
                              default=fs,
                              valid=gs,
                              typecode=cs
                              )
    elif im['data_type'] == 'finetime':
        cs = im['typecode'] if 'typecode' in im else None
        ret = DateParameter(value=value,
                            description=im['description'],
                            default=fs,
                            valid=gs,
                            typecode=cs
                            )
    elif DataTypes[im['data_type']] in ['int', 'float', 'Vector', 'Vector2D', 'Quaternion']:
        us = im['unit'] if 'unit' in im else ''
        cs = im['typecode'] if 'typecode' in im else None
        ret = NumericParameter(value=value,
                               description=im['description'],
                               typ_=im['data_type'],
                               unit=us,
                               default=fs,
                               valid=gs,
                               typecode=cs,
                               )
    else:
        ret = Parameter(value=value,
                        description=im['description'],
                        typ_=im['data_type'],
                        default=fs,
                        valid=gs,
                        )
    return ret
