# -*- coding: utf-8 -*-

from ..utils.common import mstr
from .listener import DatasetListener
from .datawrapper import DataWrapperMapper
from .composite import Composite
from .annotatable import Annotatable
from .attributable import Attributable


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

    def toString(self, level=0,
                 tablefmt='rst', tablefmt1='simple', tablefmt2='simple',
                 matprint=None, trans=True, beforedata='', **kwds):
        """ matprint: an external matrix print function
        trans: print 2D matrix transposed. default is True.
        """
        cn = self.__class__.__name__
        s = '=== %s (%s) ===\n' % (cn, self.description if hasattr(
            self, 'descripion') else '')
        s += mstr(self.__getstate__(), level=level,
                  excpt=['description'],
                  tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                  matprint=matprint, trans=trans,
                  **kwds)
        d = cn + '-datasets =\n'
        d += self._sets.toString(level=level,
                                 tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                                 matprint=matprint, trans=trans, **kwds)
        return '\n\n'.join((x for x in (s, beforedata, d) if len(x)))
