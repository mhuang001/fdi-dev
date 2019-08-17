# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .attributable import Attributable
from .annotatable import Annotatable
from .composite import Composite
from .datawrapper import DataWrapperMapper
from .listener import DatasetListener


class AbstractComposite(Attributable, Annotatable, Composite, DataWrapperMapper, DatasetListener):
    """ an annotatable and attributable subclass of Composite. 
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def __repr__(self):
        ''' meta and datasets only show names
        '''
        s = '{'
        s += 'meta = "%s", _sets = %s}' % (
            str(self.meta),
            str(self.keySet())
        )
        return s

    def toString(self):
        s = '{'
        s += 'meta = %s, _sets = %s}' % (
            self.meta.toString(),
            self._sets.__str__()
        )
        return s
