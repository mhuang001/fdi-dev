# -*- coding: utf-8 -*-

import pdb


class Annotatable(object):
    """ An Annotatable object is an object that can give a
    human readable description of itself.
    """

    def __init__(self, description='UNKNOWN', **kwds):

        self.description = description
        # print(__name__ + str(kwds))
        super(Annotatable, self).__init__(**kwds)

    @property
    def description(self):
        """ xx must be a property for ``self.xx = yy`` to work in super class after xx is set as a property also by a subclass.
        """
        try:
            return self._description
        except AttributeError:
            return None

    @description.setter
    def description(self, description):
        self._description = description

    def getDescription(self):
        """ gets the description of this Annotatable object. """
        return self.description  # __getattribute__('description')

    def setDescription(self, newDescription):
        """ sets the description of this Annotatable object. """
        self.description = newDescription  # __setattr__('description', newDescription)
