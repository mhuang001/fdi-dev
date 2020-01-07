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
from .odict import bstr
from .ndprint import ndprint


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

    def toString(self, matprint=None, trans=True, beforedata=''):
        if matprint is None:
            matprint = ndprint

        s = '# ' + self.__class__.__name__ + '\n' +\
            '# description = "%s"\n# meta = %s\n' % \
            (str(self.description), bstr(self.meta))
        d = '# data = \n\n'
        d += self._sets.toString(matprint=matprint, trans=trans)
        return s + beforedata + d
