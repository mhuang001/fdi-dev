# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class MetaDataHolder(object):
    """ Object holding meta data. 
    mh: object for compatibility with python2
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        # print(self.__dict__)

    def getMeta(self):
        """ Returns the current MetaData container of this object. """
        return self._meta
