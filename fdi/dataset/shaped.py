# -*- coding: utf-8 -*-

from ..utils.common import findShape

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Shaped():
    """ An object of specifiable kinds.

    This class is for parameters, not for products/datasets to make 'shape' MDP.
    """

    def __init__(self, **kwds):
        """ Has a shape.
        Parameters
        ----------

        Returns
        -------
        """

        # print(__name__ + str(kwds))
        super().__init__(**kwds)

    def updateShape(self, **kwds):

        self.__setattr__('shape', findShape(self.data, **kwds))
        # this is not working for the firist call as shape is not in
        # `attributable.__init__`s initializing list because 'shape'
        # is not in `ArrayDAtaset.init` args.
        # self.shape = findShape(self.data, **kwds)
        return self.shape
