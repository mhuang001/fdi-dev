# -*- coding: utf-8 -*-

from collections import ChainMap
import os
from copy import copy

from .metadataholder import MetaDataHolder
from .metadata import AbstractParameter, Parameter
from .datatypes import DataTypes
from .deserialize import Class_Look_Up

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

MdpInfo = {}


""" Names not for mormal properties. """
Reserved_Property_Names = ['history', 'meta', 'refs', 'dataset',
                           'zInfo', '_MDP', 'extraMdp', 'alwaysMeta']

""" These MetaData Parameters (MDPs) and vital attrbutes are Set By Parent classes:
| Special MDPs and attrbutes | set by parent Classes | attribute holder |
| 'meta' | `Attributable` | `_meta` |
| 'description' | `Annotatable` | `description` |
| 'data' and 'shape' | `DataWrapper` | `_data` |
| 'listeners' | `EventSender` | `_listener` |
"""
MDP_Set_by_Parents = {'meta': '_meta',
                      'description': 'description',
                      'data': '_data',
                      'listeners': '_listeners'}


class Attributable(MetaDataHolder):
    """ An Attributable object is an object that has the
    notion of meta data.

    MetaData Porperties (MDPs) are Attributes that store their properties in te metadata table.
    """

    def __init__(self, meta=None, zInfo=None, alwaysMeta=False, **kwds):
        """ Pick out arguments listed in zInfo then put updated parameters into MetaData meta.

        meta: meta data container.
        zInfo: configuration
        alwaysMeta: always treat parameters as MetaDataProperties (MDPs).
        """

        self.alwaysMeta = alwaysMeta
        self.extraMdp = {}
        self.zInfo = zInfo if zInfo else {'metadata': {}}

        # super set of args and Model. Values only.
        # if an MDP is set to None in args, use its Model default
        mdps = {}
        zm = self.zInfo['metadata']
        for x in zm:
            # 'type' in args is 'typ_'. put `type` back.
            _x = 'typ_' if x == 'type' else x
            if _x not in kwds:
                if _x in MDP_Set_by_Parents:
                    raise KeyError(
                        f'{_x} is in MDP_Set_by_Parents but missing in keywords.')
                else:
                    mdps[x] = zm[x]['default']
            else:
                # _x in kwds
                if _x not in MDP_Set_by_Parents:
                    kwval = kwds.pop(_x)
                    mdps[x] = zm[x]['default'] if kwval is None else kwval
                else:
                    # not in keywords args but in MDP_Set_by_Parents
                    # will be consumed and setattr'ed by some init call down the MRO.
                    pass
        # merge extra MDP there may be and Model MDPs.
        self._MDP = ChainMap(self.extraMdp, zm)
        # This will set MDP_Set_by_Parents args.

        super().__init__(meta=meta, **kwds)
        # do not set MDPs that have been set by super classes
        for p in copy(mdps):
            if p in self._meta:
                mdps.pop(p)
        self.setParameters(mdps)

    def setParameters(self, params):
        """ Set a group of name-value pairs to the object as properties.

        params: a dictionary of name:value where value is a subclass of
        `AbstractParameter`. value can be the value of a registered MDP.
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
        """
        Parameters
        ----------

        Returns
        -------

        """
        return self.getMeta()

    @meta.setter
    def meta(self, newMetadata):
        """
        Parameters
        ----------

        Returns
        -------

        """
        self.setMeta(newMetadata)

    def setMeta(self, newMetadata):
        """ Replaces the current MetaData with specified argument.

        Product will override this to add listener when meta is
        replaced.
        `_defaults` which usually is `self.zInfo` is added to new meta so `str(meta)` can ommit the parameters with default value.

        Parameters
        ----------
        Returns
        ------- 
        """

        defs = self.zInfo['metadata'] if hasattr(self, 'zInfo') else None
        newMetadata._defaults = defs
        self._meta = newMetadata

    def __getattribute__(self, name):
        """ Returns the named metadata parameter.

        Reads meta data table when Attributes are
        read, and returns the values only.
        """
        # print('getattribute ' + name)

        # print('aa ' + selftr(self.getMeta()[name]))

        if name not in Reserved_Property_Names:
            try:
                if name in self._MDP:
                    return self._meta[name].getValue()
            except AttributeError:
                pass

        return super().__getattribute__(name)

    def setMdp(self, name, value, met=None):

        m = self.getMeta()
        # print('MDP ', name, value, id(m), len(m))
        if name in m:
            # meta already has a Parameter for name
            p = m[name]
            if issubclass(value.__class__, AbstractParameter):
                tv, tp = value.getType(), p.getType()
                if issubclass(Class_Look_Up[DataTypes[tv]],
                              Class_Look_Up[DataTypes[tp]]):
                    p = value
                    return
                else:
                    vs = value.value
                    raise TypeError(
                        "Parameter %s type is %s, not %s's %s." % (vs, tv, name, tp))
            else:
                # value is not a Parameter
                v_type = type(value)
                p_type = Class_Look_Up[DataTypes[p.getType()]]
                if value is None or issubclass(v_type, p_type):
                    p.setValue(value)
                    return
                else:
                    vs = value
                    raise TypeError(
                        "Value %s type is %s, not %s's %s." % (vs, v_type.__name__, name, p_type.__name__))
        else:
            # named parameter is not in meta

            if issubclass(value.__class__, AbstractParameter):
                # value is a parameter
                m[name] = value
                return
            # value is not  a Parameter make one.
            m[name] = value2parameter(name, value, met)
        return

    def __setattr__(self, name, value):
        """ Stores value to attribute with name given.

        If name is in the Model (`zInfo` list), store the value in a Parameter in
        the metadata container. Updates the `_MDP' table. Updates value only, if
        an MDP attribute already has its Parameter in metadata.

        value: Must be Parameter/NumericParameter if this is normal metadata,
        depending on if it is `Number`. `Value` is the value if the  attribute
        is an MDP

        If ```self.alwaysMeta is True``` all properties of :class:`AbstractParameter` are taken as MDPs except those named in ```Reserved_Property_Names```
        """
        # if self.__class__.__name__ == 'CompositeDataset' and name == '_STID':
        #    __import__('pdb').set_trace()

        #print('setattr ' + name, value)
        if name in Reserved_Property_Names:
            super().__setattr__(name, value)
            return
        try:
            if self.alwaysMeta:
                if issubclass(value.__class__, AbstractParameter):
                    # taken as an MDP attribute . store in meta
                    self.extraMdp[name] = value
                    self.setMdp(name, value, self._MDP)
                    # assert self.meta[name].value == value
                    # must return without updating self.__dict__
                    return
            if name in self._MDP:
                # an MDP attribute like 'description'. store in meta
                self.setMdp(name, value, self._MDP)
                # assert self.meta[name].value == value
                # must return without updating self.__dict__
                return
        except AttributeError:
            pass

        super(Attributable, self).__setattr__(name, value)

    def __delattr__(self, name):
        """ Refuses deletion of mandatory attributes.
        """

        try:
            if self.alwaysMeta or \
               name in self.zInfo or \
               name in Reserved_Property_Names:
                logger.warning(
                    'Cannot delete MetaData Property or Reserved_Property_Names: ' + name)
                return
        except AttributeError:
            pass

        super(Attributable, self).__delattr__(name)

    def makeMdpMethods(self, outputfile=None):
        """ Generates a mix-in class file according to MetaData Property list.

        """
        filename = 'properties_' if outputfile is None else outputfile
        filename += self.__class__.__name__ + '.py'
        pth = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(pth, filename), 'w') as f:
            f.write('# -*- coding: utf-8 -*-\n')
            f.write(
                '\n### Automatically generated by %s.makeMdpMethods(). Do Not Edit.###' % self.__class__.__name__)
            f.write('\n\nclass MetaDataProperties():\n')
            s = make_class_properties(self.zInfo['metadata'].keys())
            f.write(s + '\n')


def value2parameter(name, value, descriptor):
    """ returns a parameter with correct type and attributes according to its value and name.

    value: type must be compatible with data_type. For example [0, 0] is wrong; Vector2d([0, 0)] is right if ``data_type``==``vector2d``.
    descriptor: is zInfo('metadata'] or zInfo['dataset'][xxx]
    """

    # if descriptor is None:
    #     im = {'description': 'UNKNOWN',
    #           'data_type': DataTypeNames[type(value).__name__],
    #           }
    # else:
    im = descriptor[name]  # {'dats_type':..., 'value':....}
    # in ['integer','hex','float','vector','quaternion']

    ext = dict(im)
    fs = im.get('default', None)
    gs = im.get('valid', None)
    ext.pop('value', '')
    ext.pop('description', '')
    ext.pop('data_type', '')
    ext.pop('default', '')
    ext.pop('valid', '')
    if im['data_type'] == 'string':
        from .stringparameter import StringParameter
        cs = im.get('typecode', 'B')
        ext.pop('typecode', '')
        ret = StringParameter(value=value,
                              description=im['description'],
                              default=fs,
                              valid=gs,
                              typecode=cs,
                              **ext,
                              )
    elif im['data_type'] == 'finetime':
        from .dateparameter import DateParameter
        ret = DateParameter(value=value,
                            description=im['description'],
                            typ_=im['data_type'],
                            default=fs,
                            valid=gs,
                            **ext,
                            )
    elif DataTypes[im['data_type']] in ['int', 'float', 'Vector', 'Vector2D', 'Quaternion']:
        from .numericparameter import NumericParameter
        us = ext.pop('unit', '')
        cs = ext.pop('typecode', '')
        ret = NumericParameter(value=value,
                               description=im['description'],
                               typ_=im['data_type'],
                               unit=us,
                               default=fs,
                               valid=gs,
                               typecode=cs,
                               **ext,
                               )
    elif DataTypes[im['data_type']] in ['bool']:
        from .numericparameter import BooleanParameter
        ext.pop('unit', '')
        ext.pop('typecode', '')
        ret = BooleanParameter(value=value,
                               description=im['description'],
                               default=fs,
                               valid=gs,
                               **ext,
                               )
    else:
        ret = Parameter(value=value,
                        description=im['description'],
                        typ_=im['data_type'],
                        default=fs,
                        valid=gs,
                        **ext,
                        )
    return ret


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
            self.setMdp(n, value, MdpInfo)

        def d(self, n=name):
            logger.warn('Cannot delete MetaData Property ' + n)
        setattr(cls, name, property(
            g, s, d, 'MetaData Property ' + name))
    return cls


def make_class_properties(attrs, reserved=None):
    """ Generates class properties source code string according to given attribute names.

    """
    pr = []
    if reserved is None:
        reserved = Reserved_Property_Names
    for x in attrs:
        if x in reserved:
            raise NameError('"%s" is a reserved property name.' % x)
        arg = x        # x + '_' if x == 'type' else x
        pr.append('    @property')
        pr.append('    def %s(self): pass' % x)
        # pr.append('        return self._meta["%s"].getValue()\n' % x)
        # pr.append('    @%s.setter' % x)
        # pr.append('    def %s(self, p):' % x)
        # pr.append('        self.setMdp("%s", p, self._MDP)\n' % x)
    pr.append('    pass')
    properties = '\n'.join(pr)
    return properties


class MetaDataProperties():
    """ Mix-in place-holder for Class denifitions that has not their own `property.py` generated by :meth: `makeMdpMethods`.
    """

    pass
