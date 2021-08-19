# -*- coding: utf-8 -*-
from .urn import Urn
from fdi.dataset.odict import ODict
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Taggable(object):
    """
    Definition of services provided by a product storage supporting tagging.
    """

    def __init__(self, **kwds):
        super(Taggable, self).__init__(**kwds)
        # {tag->{'urns':[urn]}

        # {urn->{'tags':[tag], 'meta':meta}}

    def getTags(self, urn=None):
        """ 
        Get all of the tags that map to a given URN.
        Get all known tags if urn is not specified.
        mh: returns an iterator.
        """
        raise NotImplementedError

    def getTagUrnMap(self):
        """
        Get the full tag->urn mappings.
        mh: returns an iterator
        """
        raise NotImplementedError

    def getUrn(self, tag):
        """
        Gets the URNs corresponding to the given tag. Returns an empty list if tag does not exist.
        """
        raise NotImplementedError

    def getUrnObject(self, tag):
        """
        Gets the URNobjects corresponding to the given tag.
        """
        raise NotImplementedError

    def removekey(self, key, themap, thename, othermap, othername):
        """
        Remove the given key.
        """
        raise NotImplementedError

    def removeTag(self, tag):
        """
        Remove the given tag from the tag and urn maps.
        """
        raise NotImplementedError

    def removeUrn(self, urn):
        """
        Remove the given urn from the tag and urn maps.
        """
        raise NotImplementedError

    def setTag(self, tag,  urn):
        """
        Sets the specified tag to the given URN.
        """
        raise NotImplementedError

    def tagExists(self, tag):
        """
        Tests if a tag exists.
        """
        raise NotImplementedError
