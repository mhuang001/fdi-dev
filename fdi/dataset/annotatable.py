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
        return self.getDescription()

    @description.setter
    def description(self, description):
        self.setDescription(description)

    def getDescription(self):
        """ gets the description of this Annotatable object. """
        return self._description

    def setDescription(self, newDescription):
        """ sets the description of this Annotatable object. """
        self._description = newDescription
        return
