# -*- coding: utf-8 -*-
class Annotatable(object):
    """ An Annotatable object is an object that can give a
    human readable description of itself.
    """

    def __init__(self, description='UNKNOWN', **kwds):

        self.description = description
        # print(__name__ + str(kwds))
        super(Annotatable, self).__init__(**kwds)

    def a__init__(self,  *args, description='UNKNOWN', **kwds):

        ls = list(args)
        if len(ls) == 1 and isinstance(ls[0].__class__, str) and description == 'UNKNOWN':
            self.description = ls[0]
        else:
            if len(ls) > 1:
                raise TypeError(
                    'No more than one positional argument allowed.')
            self.description = description
        # print(__name__ + str(kwds))
        super(Annotatable, self).__init__(**kwds)

    def getDescription(self):
        """ gets the description of this Annotatable object. """
        return self.description

    def setDescription(self, newDescription):
        """ sets the description of this Annotatable object. """
        self.description = newDescription
        return
