# -*- coding: utf-8 -*-
from .ndprint import ndprint
from .odict import bstr
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
        super(AbstractComposite, self).__init__(**kwds)

    def __repr__(self):
        ''' meta and datasets only show names
        '''
        s = '{'
        s += 'meta = "%s", _sets = %s}' % (
            str(self.meta),
            str(self.keySet())
        )
        return s

    def toString(self, matprint=None, trans=True, beforedata='', level=0):
        if matprint is None:
            matprint = ndprint

        s = '# ' + self.__class__.__name__ + '\n' +\
            '# description = "%s"\n# meta = %s\n' % \
            (str(self.description), bstr(self.meta, level=level))
        d = '# data = \n\n'
        d += self._sets.toString(matprint=matprint, trans=trans, level=level)
        return s + beforedata + d
