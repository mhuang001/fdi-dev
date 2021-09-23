# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)


class Annotatable():
    """ An Annotatable object is an object that can give a
    human readable description of itself.
    """

    def __init__(self, description='UNKNOWN', **kwds):
        """

        Parameters
        ----------

        Returns
        -------

        """

        # print(__name__ + str(kwds))
        super().__init__(**kwds)  # Annotatable
        self.description = description

    @property
    def xdescription(self):
        """ xx must be a property for ``self.xx = yy`` to work in super class after xx is set as a property also by a subclass.

        Parameters
        ----------

        Returns
        -------

        """
        try:
            return self._description
        except AttributeError:
            return None

    @xdescription.setter
    def xdescription(self, description):
        """ Property of the description of this Annotatable object.

        Parameters
        ----------
        description : string
                         The new description.

        Returns
        -------

        """

        self._description = description

    def getDescription(self):
        """ gets the description of this Annotatable object.

        Parameters
        ----------

        Returns
        -------
        string:
              The current description.
        """
        return self.description

    def setDescription(self, newDescription):
        """ sets the description of this Annotatable object.

        Parameters
        ----------
        newDescription : string
                         The new description.

        Returns
        -------

        """
        self.description = newDescription
