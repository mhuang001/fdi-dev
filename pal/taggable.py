# -*- coding: utf-8 -*-
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

from .urn import Urn


class Taggable():
    """
    Definition of services provided by a product storage supporting versioning.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self._tags = dict()
        self._urns = dict()

    def getTags(self, urn=None):
        """ Get all known tags if urn is not specified.
        Get all of the tags that map to a given URN.
        mh: returns an iterator.
        """
        if urn is None:
            return self._tags.keys()
        #uobj = Urn(urn=urn)
        return self._urns[urn]

    def getTagUrnMap(self):
        """
        Get the full tag->urn mappings.
        """
        return self._tags

    def getUrnObject(self, tag):
        """
        Gets the URNobjects corresponding to the given tag.
        """
        l = [Urn(x) for x in self._tags(tag)]
        return l

    def removekey(self, key, themap, oppmap):
        """
        Remove the given key.
        """
        vals = themap.pop(key)
        # remove all items whose v is key in the opposit map
        for val in vals:
            oppmap[val].remove(key)
            if len(oppmap[val]) == 0:
                oppmap.pop(val)

    def removeTag(self, tag):
        """
        Remove the given tag.
        """
        self.removekey(tag, self._tags, self._urns)

    def removeUrn(self, urn):
        """
        Remove the given urn from the tag-urn map.
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        self.removekey(u, self._urns, self._tags)

    def setTag(self, tag,  urn):
        """
        Sets the specified tag to the given URN.
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        if tag in self._tags:
            self._tags[tag].append(u)
        else:
            self._tags[tag] = [u]

    def tagExists(self, tag):
        """
        Tests if a tag exists.
        """
        return tag in self._tags
