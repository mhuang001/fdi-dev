# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .metadataholder import MetaDataHolder
from .metadata import MetaData


class Attributable(MetaDataHolder):
    """ An Attributable object is an object that has the
    notion of meta data. """

    def __init__(self, meta=None, **kwds):
        if meta is None:
            self.setMeta(MetaData())
        else:
            self.setMeta(meta)
        super(Attributable, self).__init__(**kwds)
        #print('**' + self._meta.toString())

    @property
    def meta(self):
        return self.getMeta()

    @meta.setter
    def meta(self, newMetadata):
        self.setMeta(newMetadata)

    def setMeta(self, newMetadata):
        """ Replaces the current MetaData with specified argument. 
        mh: Product will override this to add listener whenevery meta is
        replaced
        """
        self._meta = newMetadata
