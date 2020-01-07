# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Comparable(object):
    """
    """

    def __init__(self, **kwds):
        super(Comparable, self).__init__(**kwds)

    def compareTo(o):
        return 1 if self == o else 0
