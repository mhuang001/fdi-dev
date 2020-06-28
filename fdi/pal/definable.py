# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Definable(object):
    """
    for items being able to be defined with a Definition.
    """

    def __init__(self, **kwds):
        super(Definable, self).__init__(**kwds)
        self._definition = None

    def getDefinition(self):
        """
        Returns the definition associated to this definable item.
        mh: adopting http://herschel.esac.esa.int/hcss-doc-15.0/load/hcss_drm/api/index.html?herschel/ia/pal/ProductRef.html but parameterize definition does not seem worth it given the few numbers of implemented definitions
        """

        return self._definition
