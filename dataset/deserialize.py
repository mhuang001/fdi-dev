from collections import OrderedDict
import json

from dataset.logdict import doLogging, logdict
if doLogging:
    import logging
    import logging.config
    # create logger
    logging.config.dictConfig(logdict)
    # logconf = os.path.abspath('pnslog.conf')
    # logging.config.dictConfig(json.load(open(logconf, 'r')))
    logger = logging.getLogger(__name__)

from dataset.metadata import Parameter, NumericParameter, MetaData
from dataset.dataset import ArrayDataset, TableDataset, CompositeDataset
from dataset.product import FineTime1, History, Product

''' Note: this has to be in a different file where other interface
classes are defined to avoid circular dependency (such as ,
Serializable.
'''


def constructSerializableClassID(obj, dbg=False):
    """ mh: reconstruct object from the output of jason.loads().
    Recursively goes into nested class instances that are not
    encoded by default by JSONEncoder, instantiate and fill in
    variables.
    Objects to be deserialized must have their classes loaded.
    ClassID cannot have module names in it (e.g.  dataset.Product)
    or globals()[classname] will not work. See alternative in
    https://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname

    """
    classname = obj.__class__.__name__
    # process list first
    if issubclass(obj.__class__, list):
        if dbg:
            print('lis ' + classname)
        inst = []
        # loop i to preserve order
        for i in range(len(obj)):
            x = obj[i]
            if issubclass(x.__class__, (list, dict)):
                des = constructSerializableClassID(x)
            else:
                des = x
            inst.append(des)
        return inst

    if 'classID' not in obj:
        """ This object is supported by JSONEncoder """
        if dbg:
            print('fff ' + classname)
        inst = obj
    else:
        classname = obj['classID']
        if dbg:
            print('ccc ' + classname)
        # process types wrapped in a dict
        if classname == 'bytes':
            inst = bytes.fromhex(obj['hex'])
            return inst
        #inst = eval(classname + '()')
        inst = globals()[classname]()
    for (k, v) in obj.items():
        """ loop through all key-value pairs. """
        if k != 'classID' and k != 'version':
            # deserialize v
            if issubclass(v.__class__, (dict, list)):
                if dbg:
                    print('+++ %s %s' % (str(v.__class__), str(v)))
                desv = constructSerializableClassID(v)
            else:
                if dbg:
                    print('--- %s %s' % (str(v.__class__), str(v)))
                desv = v
            # set k with desv
            if issubclass(inst.__class__, dict):
                inst[k] = desv
                if dbg:
                    print('in %s key  %s found %s %s' %
                          (str(inst.__class__), str(k), str(desv), str(desv.__class__)))
            else:
                setattr(inst, k, desv)
                if dbg:
                    print('in %s attr %s found %s %s' %
                          (str(inst.__class__), str(k), str(desv), str(desv.__class__)))
    return inst


def deserializeClassID(js, dbg=False):
    """ Loads classes with ClassID from the results of serializeClassID
    """
    # dbg = False  # True if issubclass(obj.__class__, list) else False
    obj = json.loads(js, object_hook=OrderedDict)
    if dbg:
        # print('load-str ' + str(o) + ' class ' + str(o.__class__))
        print('obj ' + str(obj) + str(obj.__class__))

    return constructSerializableClassID(obj, dbg=dbg)
