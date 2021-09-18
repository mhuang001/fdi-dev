# -*- coding: utf-8 -*-

from ..utils.common import mstr
from .odict import ODict
from .listener import DatasetListener
from .datawrapper import DataWrapperMapper
from .composite import Composite
from .annotatable import Annotatable
from .attributable import Attributable

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class AbstractComposite(Attributable, DatasetListener, Composite, DataWrapperMapper):
    """ an annotatable and attributable subclass of Composite. 

    Composite inherits annotatable via EventListener via DataContainer. 
    """

    def __init__(self, **kwds):
        """

        Parameters
        ----------

        Returns
        -----

        """

        super().__init__(**kwds)

    def toString(self, level=0, width=0,
                 tablefmt='grid', tablefmt1='simple', tablefmt2='simple',
                 matprint=None, trans=True, beforedata='', heavy=True,
                 **kwds):
        """ matprint: an external matrix print function

        Parameters
        ----------
        trans: print 2D matrix transposed. default is True.
        -------

        """
        cn = self.__class__.__name__
        if level > 1:
            # s = '=== %s (%s) ===\n' % (cn, self.description if hasattr(
            #    self, 'description') else '')

            s = mstr(self._meta, level=level, width=width,
                     tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                     excpt=['description'], **kwds)
            s += mstr(self.data, level=level,
                      excpt=['description'],
                      tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                      matprint=matprint, trans=trans, heavy=False,
                      **kwds)
            return s
        from .dataset import make_title_meta_l0
        s, last = make_title_meta_l0(self, level=level, width=width,
                                     tablefmt=tablefmt, tablefmt1=tablefmt1,
                                     tablefmt2=tablefmt2, excpt=['description'])

        d = f'DATA {cn}'
        d += '\n' + '-' * len(d) + '\n'
        o = ODict(self.data)
        d += o.toString(level=level, heavy=False,
                        tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                        matprint=matprint, trans=trans, **kwds)
        return '\n\n'.join((x for x in (s, beforedata, d) if len(x))) + '\n' + last
