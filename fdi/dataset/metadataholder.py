# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .metadata import MetaData


class MetaDataHolder(object):
    """ Object holding meta data. 
    mh: object for compatibility with python2
    """

    def __init__(self, **kwds):
        super(MetaDataHolder, self).__init__(**kwds)
        if not hasattr(self, '_meta'):
            self._meta = MetaData()

    def getMeta(self):
        """ Returns the current MetaData container of this object. 
        Cannot become a python property because setMeta is in Attributable
        """
        return self._meta

    def hasMeta(self):
        """ whether the metadata holder is present.
        During initialization subclass of MetaDataHolder may need to know if the metadata holder has been put in place with is method.
        """

        return hasattr(self, '_meta')
