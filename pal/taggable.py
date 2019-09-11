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
        # {tag:{urn:[]}
        self._tags = dict()
        # {urn:{tags:[], 'meta':meta}
        self._urns = dict()

    def getTags(self, urn=None):
        """ 
        Get all of the tags that map to a given URN.
        Get all known tags if urn is not specified.
        mh: returns an iterator.
        """
        if urn is None:
            return self._tags.keys()
        #uobj = Urn(urn=urn)
        return self._urns[urn]['tags']

    def getTagUrnMap(self):
        """
        Get the full tag->urn mappings.
        mh: returns an iterator
        """
        return zip(self._tags.keys(), map(lambda v: v['urns'], self._value()))

    def getUrn(self, tag):
        """
        Gets the URNs corresponding to the given tag.
        """

        return self._tags[tag]['urns']

    def getUrnObject(self, tag):
        """
        Gets the URNobjects corresponding to the given tag.
        """
        l = [Urn(x) for x in self._tags[tag]['urns']]
        return l

    def removekey(self, key, themap, thename, othermap, othername):
        """
        Remove the given key.
        """
        vals = themap.pop(key)
        # remove all items whose v is key in the otherosit map
        for val in vals[othername]:
            othermap[val][thename].remove(key)
            if len(othermap[val][thename]) == 0:
                othermap[val].pop(thename)
                if len(othermap[val]) == 0:
                    othermap.pop(val)

    def removeTag(self, tag):
        """
        Remove the given tag.
        """
        self.removekey(tag, self._tags, self._urns, 'tags', 'urns')

    def removeUrn(self, urn):
        """
        Remove the given urn from the tag-urn map.
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        self.removekey(u, self._urns, self._tags, 'urns', 'tags')

    def setTag(self, tag,  urn):
        """
        Sets the specified tag to the given URN.
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        if tag in self._tags:
            if 'urn' in self._tags[tag]:
                self._tags[tag].append(u)
            else:
                self._tags[tag]['urn'] = [u]
        else:
            self._tags[tag] = {'urns': [u]}

    def tagExists(self, tag):
        """
        Tests if a tag exists.
        """
        return tag in self._tags
