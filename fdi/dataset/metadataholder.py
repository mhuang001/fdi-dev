# -*- coding: utf-8 -*-

from . import metadata

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class MetaDataHolder():
    """ Object holding meta data. 

    """

    def __init__(self, meta=None, **kwds):
        """ Adds MetaData to the class.
        with defaults set to self.zInfo['metadata'].

        Parameters
        ----------

        Returns
        -------
        """
        if meta is None:
            meta = metadata.MetaData()
        self.setMeta(meta)
        super().__init__(**kwds)

    def getMeta(self):
        """ Returns the current MetaData container of this object. 
        Cannot become a python property because setMeta is in Attributable

        Parameters
        ----------

        Returns
        -------

        """
        return self._meta

    def hasMeta(self):
        """ whether the metadata holder is present.
        During initialization subclass of MetaDataHolder may need to know if the metadata holder has been put in place with is method.

        Parameters
        ----------

        Returns
        -------

        """
        return hasattr(self, '_meta')

    def setMeta(self, meta):
        """
        Parameters
        ----------

        Returns
        -------

        """
        self._meta = meta
