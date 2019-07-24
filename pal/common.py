import filelock
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .urn import Urn
from dataset.deserialize import deserializeClassID
from dataset.product import Product, FineTime1, History
from dataset.metadata import Parameter, NumericParameter, MetaData
from dataset.dataset import GeneralDataset, ArrayDataset, TableDataset, CompositeDataset, Column


def getJsonObj(fp, usedict=False):

    with open(fp, 'r') as f:
        stri = f.read()
    # ret = json.loads(stri, parse_float=Decimal)
    # ret = json.loads(stri, cls=Decoder,
    #               object_pairs_hook=collections.OrderedDict)
    ret = deserializeClassID(stri, dglobals=globals(), usedict=usedict)
    logger.debug(str(ret)[:160] + '...')
    return ret


def getProductObject(urn):
    """ Returns a product from URN. returns object.
    """
    filep = Urn.getFullPath(urn)
    poolpath = filep.rsplit('/', maxsplit=1)[0]
    lock = filelock.FileLock(poolpath + '/lock')
    lock.acquire()
    try:
        p = getJsonObj(filep)
    except Exception as e:
        raise e
    finally:
        lock.release()
    return p
