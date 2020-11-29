# -*- coding: utf-8 -*-


from ..dataset.deserialize import deserialize
from .localpool import LocalPool
from ..utils.common import pathjoin, trbk


import filelock
import sys
import pdb
import os
from os import path as op
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
    strset = str
    from urllib.parse import urlparse, quote, unquote
else:
    PY3 = False
    strset = (str, unicode)
    from urlparse import urlparse, quote, unquote


class HttpPool(LocalPool):
    """ the pool will save all products locally on the host Http server.
    """

    def __init__(self, **kwds):
        """ creates file structure if there isn't one. if there is, read and populate house-keeping records. create persistent files if not exist.
        """
        # print(__name__ + str(kwds))
        super(HttpPool, self).__init__(**kwds)

    def xschematicLoadProduct(self, resourcetype, index, serialized=True):
        """
        like localpool but returns serialized form by default.
        """

        p = super(HttpPool, self).schematicLoadProduct(resourcetype=resourcetype,
                                                       index=index,
                                                       serialized=serialized
                                                       )
        return p
