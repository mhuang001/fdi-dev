# -*- coding: utf-8 -*-

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class InvalidType(object):
    def __repr__(self):
        return 'Invalid'


# singleton object for invalid values
INVALID = InvalidType()
