# -*- coding: utf-8 -*-

from ..utils.common import mstr
from .odict import ODict
from .listener import EventListener
from .datawrapper import DataWrapperMapper
from .composite import Composite
from .annotatable import Annotatable
from .attributable import Attributable

import logging
# create logger
logger = logging.getLogger(__name__)
#logger.debug('level %d' %  (logger.getEffectiveLevel()))


class AbstractComposite(Attributable, EventListener, Composite, DataWrapperMapper):
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
                 tablefmt='grid', tablefmt1='simple', tablefmt2='rst',
                 extra=False,
                 matprint=None, trans=True, beforedata='', heavy=True,
                 center=-1, **kwds):
        """ matprint: an external matrix print function

        Parameters
        ----------
        trans: print 2D matrix transposed. default is True.
        -------

        """
        cn = self.__class__.__name__
        if level > 1:
            s = f'{cn}('
            s += 'META: ' + mstr(self._meta, level=level, width=width,
                                 tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                                 excpt=['description'], **kwds)
            s += ' DATA: ' + mstr(self.data, level=level,
                                  excpt=['description'],
                                  tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                                  matprint=matprint, trans=trans, heavy=False,
                                  **kwds)
            return s + ')'
        from .dataset import make_title_meta_l0
        s, last = make_title_meta_l0(self, level=level, width=width,
                                     tablefmt=tablefmt, tablefmt1=tablefmt1,
                                     tablefmt2=tablefmt2,
                                     extra=extra, center=-1, excpt=['description'])
        width = len(last)-1
        ds = list(f'"{x}"' for x in self.keys())
        d = 'Total %d Sub-Datasets: %s' % (len(ds), ', '.join(ds))
        d = d.center(width) + '\n\n'  # + '-' * len(d) + '\n'
        o = ODict(self.data)
        d += o.toString(level=level, heavy=False, center=width,
                        tablefmt=tablefmt, tablefmt1=tablefmt1, tablefmt2=tablefmt2,
                        matprint=matprint, trans=trans, keyval='SubDataset ',
                        **kwds)
        return '\n\n'.join((x for x in (s, beforedata, d) if len(x))) + '\n' + last

    string = toString
