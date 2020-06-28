# -*- coding: utf-8 -*-

from ..dataset.classes import Classes
from ..dataset.deserialize import deserializeClassID
from ..dataset.eq import deepcmp
from .ydump import ydump

import json


def checkjson(obj, dbg=0):
    """ seriaizes the given object and deserialize. check equality.
    """

    # dbg = True if issubclass(obj.__class__, BaseProduct) else False

    indent = 4 if dbg > 1 else None

    if hasattr(obj, 'serialized'):
        js = obj.serialized(indent=indent)
    else:
        js = json.dumps(obj, indent=indent)

    if dbg:
        print(ydump(obj))
        print('******** checkjsom ' + obj.__class__.__name__ +
              ' serialized: ******\n')
        print(js)
        print('*************')
    des = deserializeClassID(js, lgb=Classes.mapping, debug=dbg)
    if dbg:
        if 0 and hasattr(des, 'meta'):
            print('des.mets ' + str((des.meta.listeners)))
        print('****** checkjson deserialized ' + str(des.__class__) +
              '******\n')
        # pprint(des)
        print(ydump(des))

        # js2 = json.dumps(des, cls=SerializableEncoder)
        # pprint('**** des     serialized: *****')
        # pprint(js)

        r = deepcmp(obj, des)
        print('******** deepcmp ********')
        print('identical' if r is None else r)
        # print(' DIR \n' + str(dir(obj)) + '\n' + str(dir(des)))
    if 0 and issubclass(obj.__class__, BaseProduct):
        print(str(id(obj)) + ' ' + obj.toString())
        print(str(id(des)) + ' ' + des.toString())
        # obj.meta.listeners = []
        # des.meta.listeners = []
    assert obj == des, deepcmp(obj, des) + deepcmp(obj, des)
    return des
