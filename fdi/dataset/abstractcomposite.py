# -*- coding: utf-8 -*-

from ..utils.common import mstr
from .listener import DatasetListener
from .datawrapper import DataWrapperMapper
from .composite import Composite
from .annotatable import Annotatable
from .attributable import Attributable

import pdb

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class AbstractComposite(Attributable, Annotatable, Composite, DataWrapperMapper, DatasetListener):
    """ an annotatable and attributable subclass of Composite. 
    """

    def __init__(self, **kwds):
        # pdb.set_trace()
        super(AbstractComposite, self).__init__(**kwds)

    def __repr__(self, **kwds):
        ''' toString(level=1, **kwds)
        '''
        return self.toString(level=1, **kwds)

    def toString(self, level=0, matprint=None, trans=True, beforedata='', **kwds):
        """ matprint: an external matrix print function
        trans: print 2D matrix transposed. default is True.
        """
        cn = self.__class__.__name__
        s = '# ' + cn + '\n' +\
            mstr(self.__getstate__(), level=level, **kwds)
        d = cn + '-datasets =\n'
        d += self._sets.toString(level=level,
                                 matprint=matprint, trans=trans, **kwds)
        return '\n\n'.join((x for x in (s, beforedata, d) if len(x)))
