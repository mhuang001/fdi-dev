# -*- coding: utf-8 -*-
class Annotatable():
    """ An Annotatable object is an object that can give a
    human readable description of itself.
    """

    def __init__(self, description='UNKNOWN', **kwds):
        self.description = description
        super().__init__(**kwds)

    def getDescription(self):
        """ gets the description of this Annotatable object. """
        return self.description

    def setDescription(self, newDescription):
        """ sets the description of this Annotatable object. """
        self.description = newDescription
        return
