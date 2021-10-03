# -*- coding: utf-8 -*-

from .ydump import ydump
from ..dataset.classes import Classes
from ..dataset.serializable import serialize
from ..dataset.deserialize import deserialize
from ..dataset.eq import deepcmp
import json
import sys
from pprint import pprint


def getyaml():
    if 0:
        import inspect
        import collections
        import ruamel
        from ruamel.yaml import YAML
        from ruamel.yaml.representer import RoundTripRepresenter

        ruamel.yaml.add_representer(
            Classes.mapping['ODict'], RoundTripRepresenter.represent_dict)

        ruamel.yaml.add_representer(collections.OrderedDict,
                                    RoundTripRepresenter.represent_dict)
        yaml = YAML(typ='rt')
        yaml.default_flow_style = False
        from ..dataset.classes import Classes
        for n, c in Classes.mapping.items():
            if inspect.isclass(c):
                print(n+' %s' % type(c).__name__)
                yaml.register_class(c)
    else:
        from .ydump import ydump, yinit
        yinit()


def checkjson(obj, dbg=0, **kwds):
    """ seriaizes the given object and deserialize. check equality.
    """

    # dbg = True if issubclass(obj.__class__, BaseProduct) else False

    if not dbg:
        js = serialize(obj)
    else:
        js = serialize(obj, indent=4)

        print('<<<<<*** checkjsom ' + obj.__class__.__name__ +
              ' serialized: ******\n')
        print(js)
        print('***>>>>>')

    des = deserialize(js, lookup=Classes.mapping, debug=dbg)
    if dbg:
        if 0 and hasattr(des, 'meta'):
            print('des.meta ' + str((des.meta.listeners)))
        print('****** checkjson deserialized ' + str(des.__class__) +
              '******\n')
        try:
            if 0:
                yaml.dump(des, sys.stdout)
            else:
                print(des.yaml())
        except:
            print('ydump of deserialized obj failed')
            pprint(des)

        # js2 = json.dumps(des, cls=SerializableEncoder)
        # pprint('**** des     serialized: *****')
        # pprint(js)

        r = deepcmp(obj, des, **kwds)
        print('******** deepcmp ********')
        print('identical' if r is None else r)
        # print(' DIR \n' + str(dir(obj)) + '\n' + str(dir(des)))
        assert r is None
    if 0 and issubclass(obj.__class__, BaseProduct):
        print(str(id(obj)) + ' ' + obj.toString())
        print(str(id(des)) + ' ' + des.toString())
        # obj.meta.listeners = []
        # des.meta.listeners = []

    assert obj == des, deepcmp(obj, des, **kwds)
    return des
