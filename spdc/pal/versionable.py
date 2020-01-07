# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Versionable(object):
    """
    for items being able to be defined with a Definition.
    """

    def __init__(self, **kwds):
        super(Versionable, self).__init__(**kwds)

    def getLastVersion(self, ref):
        """
        Returns the latest version of the given ProductRef.
        """

        return None

    def getVersions(self, ref):
        """
        Returns all the versions of the given ProductRef.
        """

        return []

    def saveProductRef(self, ref):
        """
        Saves the product referenced and returns the designated URN.
        """

        return None
