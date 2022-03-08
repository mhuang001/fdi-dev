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
        super(DictHk, self).__init__(**kwds)
        # {tag->{'urns':[urn]}
        self._tags = dict()
        # {urn->{'tags':[tag], 'meta':meta}}
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
        csdb: csdb/v1/storage/tag?tag=tag1,tag2
        """
        return zip(self._tags.keys(), map(lambda v: v['urns'], self._value()))

    def getUrn(self, tag):
        """
        Gets the URNs corresponding to the given tag. Returns an empty list if tag does not exist.
        curl -X GET "http://123.56.102.90:31702/csdb/v1/storage/info?urns=urn%3Apoolbs%3A20211018%3A1" -H "accept: */*"
        """
        # TODO: return all urna if tag is none?
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
        vals = themap.pop(key, [])
        # remove all items whose v is key in the otherosit map
        for val in vals[othername]:
            othermap[val][thename].remove(key)
            # if we have just removed the last key, remove the empty dict
            if len(othermap[val][thename]) == 0:
                othermap[val].pop(thename)
                # if this caused the othermap[val] to be empty, remove the empty dict
                if len(othermap[val]) == 0:
                    othermap.pop(val)

    def removeTag(self, tag):
        """
        Remove the given tag from the tag and urn maps.
        # TODO in CSDB
        """
        self.removekey(tag, self._tags, 'tags', self._urns, 'urns')

    def removeUrn(self, urn):
        """
        Remove the given urn from the tag and urn maps.

        Only changes maps in memory, not on disk.
        curl -X POST "http://123.56.102.90:31702/csdb/v1/storage/delete?path=%2Fpoolbs%2Ffdi.dataset.product.Product%2F24" -H "accept: */*"
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        self.removekey(u, self._urns, 'urns', self._tags, 'tags')

    def setTag(self, tag,  urn):
        """
        Sets the specified tag to the given URN.
        # TODO in CSDB
        """
        u = urn.urn if issubclass(urn.__class__, Urn) else urn
        if u not in self._urns:
            raise ValueError(urn + ' not found in pool ' + self._poolname)
        else:
            self._urns[u]['tags'].append(tag)

        if tag in self._tags:
            self._tags[tag]['urns'].append(u)
        else:
            self._tags[tag] = dict(urns=[u])

    def tagExists(self, tag):
        """
        Tests if a tag exists.
        # TODO in CSDB
        """
        return tag in self._tags
