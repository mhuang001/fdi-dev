# -*- coding: utf-8 -*-
from .taggable import Taggable
from .urn import Urn
from fdi.dataset.odict import ODict
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class DictHk(Taggable):
    """
    Definition of services provided by a product storage supporting versioning.
    """

    def __init__(self, **kwds):
        super(Taggable, self).__init__(**kwds)
        # {tag->{'urns':[urn]}
        self._tags = ODict()
        # {urn->{'tags':[tag], 'meta':meta}}
        self._urns = ODict()

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
        Gets the URNs corresponding to the given tag. Returns an empty list if tag does not exist.
        """
        if tag not in self._tags:
            return []
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
        Remove the given tag from the tag and urn maps.
        """
        self.removekey(tag, self._tags, 'tags', self._urns, 'urns')

    def removeUrn(self, urn):
        """
        Remove the given urn from the tag and urn maps.
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        self.removekey(u, self._urns, 'urns', self._tags, 'tags')

    def setTag(self, tag,  urn):
        """
        Sets the specified tag to the given URN.
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        if u not in self._urns:
            raise ValueError(urn + ' not found in pool')
        else:
            self._urns[urn]['tags'].append(tag)

        if tag in self._tags:
            self._tags[tag]['urns'].append(u)
        else:
            self._tags[tag] = ODict(urns=[u])

    def tagExists(self, tag):
        """
        Tests if a tag exists.
        """
        return tag in self._tags
