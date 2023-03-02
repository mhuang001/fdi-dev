# -*- coding: utf-8 -*-
from .taggable import Taggable
from .urn import Urn, parseUrn, makeUrn
from .productpool import ProductPool

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

# List of Housekeeping DBs
# HKDBS = ['classes', 'tags', 'urns', 'dTypes', 'dTags']
# some new ####
HKDBS = ['dTypes', 'dTags']

""" Reference Data Model for ManagedPool.

The Housekeeping Tables v2.0: `dTypes` and `dTags`
--------------------------------------------------

The FDI `ProductPool` stors data and their references.
The products are organized using their Data Type name, e.g. `fdi.dataset.product.Product`, in the Housekeeping table named `dTypes`. 

When initialized, the `dTypes` table is empty mapping. When a data item is saved in the pool, `dTypes` gets a key named by the Data Type, with a mapping (DTM) as the key's value to hold other information of the data. Every DTM has two entries: 'sn' and 'currentSN'.

Every data item of a certain Data Type is given a serial number (sn) to index identify it within the DMT, which uses the serial numbers as the key and a mapping (SNM) to hold information of this product: `tags` list, optionally `meta` for metadata access, and `refcnt` for refereced state. The latest allocated serial number is recorded with the 'currentSN' key in the DTM. Every data item added to the pool increments 'currentSN' of the data type by 1.

When a data item is removed, its serial number, with its SNM, are removed from its associated DTM.

All data are cleared by initialization. Removing all items within a DTM does not reset its `currentSN`. For example if you::

   * add a Product of a new type, you will get ``sn=0, currentSN=0``.
   * remove it and the size of the SNM becomes 0 and `currentSN` stay the same.
   * add it again, you will get ``sn=1, currentSN=1``.

`dTypes` schematics::

.. code-block:: 

                     $Datatype_Name0:
                            'currentSN': $csn
                            'sn':
                                $sn0:
                                   tags: {$tag1, $tag2, ...
                                   meta: [$start, $end]
                                   refcnt: $count
                                $sn1:
                                   tags: {$tag1, $tag2, ...
                                   meta: [$start, $end]
                                   refcnt: $count

               example::

                    'foo.bar.Bar':
                            'currentSN': 1
                            'sn':
                                0:
                                   'tags': {'cat', 'white'}
                                   'meta': [123, 456]
                                   'refcnt': 0
                                1:
                                   'tags': {'dog', 'white'}
                                   'meta': [321, 765]
                                   'refcnt': 0
                    'foo.baz.Baz':
                            'currentSN': 34
                            'sn':
                                34:
                                   'tags': {'tree', 'green'}
                                   'meta': [100, 654]
                                   'refcnt': 1

The `dTags` table is the other table of the Pool.  Itdiffers from `tags` in v1:;

    1. uses `dTypes:[sn]`, instead of `urn`, so there is no poolname anywhere,
    2. simplify by removing second level dict.

When a data item is saved with one or multiple tag strings. The key is the tag (iterate if there are more than one tag), the value is the Tags MApping (TM). The Data Type is the key in the TM, the value is a list sn number from filling the `dTypes` table is appended to the list. When this data item is removed, so is its entry in the list. If the list is empty, the Data Type is removed from `dTags`.

The schematic of the `dTags` table is::

.. code::

                     $tag_name0:
                           $Datatype_Name1:{$sn1, $sn2...}
                           $Datatype_Name2:{$sn3, ...}

example::

                     'cat': { 'foo.bar.Bar':{0} }
                     'white': { 'foo.bar.Bar'; {0, 1} }
                     'dog': ...
"""


def get_missing(self, urn, datatype, sn, no_check=False,
                int_index=True):
    """ make URN(s) if datatype and sn(s) are given and vice versa.

    Parameters
    ----------
    int_index : bool
       Set `True` to return integer `sn` (Default)
    no_check: bool
        Do not Check if `datatype` and `sn` are in the pool's HK.
        Default is `False`
    Return
    ------
    tuple
    str, str, int
        Refer tp `parseUrn`.

    Raises
    ------
    ValueError if urn not found or not from this pool.
    KeyError if datatype does not exist.
    IndexError if sn does not exist.
    """
    if urn is None and datatype is None and sn is None:
        return None, None, None

    if datatype is None or sn is None and urn is not None:
        # new ###
        poolname, datatype, sn = parseUrn(urn, int_index=int_index)
    else:
        # datatype+sn takes priority over urn
        urn = makeUrn(self._poolname, datatype, sn)

    u = urn.urn if issubclass(urn.__class__, Urn) else urn
    # new ###
    if not no_check:
        dat = datatype
        sns = sn
        if not issubclass(sn.__class__, (list, tuple)):
            dat = [datatype]
            sns = [sn]
            for d, s in zip(dat, sns):
                if hasattr(self, 'serverDatatypes') and d not in self.serverDatatypes:
                    raise KeyError(
                        f'{d} not found on server{self._poolname}')
                if d not in self._dTypes or s not in self._dTypes[d]['sn']:
                    raise IndexError('%s:%d not found in pool %s.' %
                                     (d, s, self._poolname))
    # /new ###
    if 0:
        if u not in self._urns:
            raise ValueError(urn + ' not found in pool ' + self._poolname)
    return u, datatype, sn


def add_tag_datatype_sn(tag, datatype, sn, dTypes=None, dTags=None):
    """Static function to  add a tag to datatype-sn to pool fmt 2.0

    Parameters
    ----------
    tag : str
        A tag. Multiple tags have to make multiple calls. `None` and empty tags are ignored.
    datatype : str
        The class name of the data item, new or existing.
    sn : int
        The serial number in integer.
    dTypes : dict
        the first nested mapping of pool fmt 2.
    dTags : dict
        the tag mapping of pool fmt 2.

    """
    if not tag:
        return

    if not isinstance(sn, int):
        raise TypeError('serial number must be an integer.')
    snt = dTypes[datatype]['sn'][sn].get('tags', set())
    if isinstance(snt, list):
        snt = set(snt)
    # if tag not in snt:
    snt.add(tag)
    dTypes[datatype]['sn'][sn]['tags'] = snt  # newly created {tag..}
    # dTags saves datatype:sn
    typ = datatype
    if tag not in dTags:
        dTags[tag] = {}
    t = dTags[tag]
    if typ not in t:
        t[typ] = {str(sn)}
    else:
        if isinstance(t[typ], list):
            t[typ] = set(t[typ])
        t[typ].add(str(sn))


def populate_pool2(tags, ptype, sn=None, dTypes=None, dTags=None):
    """Add a new product to Housekeeping Tables v2.

    A new product is representated by its type name and optional
    serial number (aka Index), and tags.

    Parameters
    ----------
    tags : list
        The tags in a list. `None` and empty tags are ignored.
    ptype : str
        The product name / datatype / class name of the data item, new or existing.
    sn : str
        Serial number. If is `None`, it is assigned as the one in `dTypes`.

    Returns
    -------
    tuple
        dTypes and dTags with updates, and the index/serial number
    """

    # new ###
    if dTypes is None:
        dTypes = {}
    if dTags is None:
        dTags = {}

    if ptype in dTypes:
        if sn is None:
            int_sn = dTypes[ptype]['currentSN'] + 1
        else:
            int_sn = int(sn)
    else:
        int_sn = 0 if sn is None else int(sn)
        dTypes[ptype] = {
            'currentSN': int_sn,
            'sn': {}
        }

    snd = dTypes[ptype]['sn']
    _sn = str(int_sn)
    if int_sn not in snd:
        snd[int_sn] = {
        }

    dTypes[ptype]['currentSN'] = int_sn

    # /new #####
    if tags is not None:
        for t in tags:
            add_tag_datatype_sn(t, ptype, int_sn, dTypes, dTags)

    return dTypes, dTags, _sn


class DictHk(ProductPool):
    """
    Definition of services provided by a product storage supporting versioning.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)
        # self._dTypes = dict()

    def setup(self):
        """ Sets up interal machiney of this Pool,
        but only if self._poolname and self._poolurl are present,
        and other pre-requisits are met.

        Subclasses should implement own setup(), and
        make sure that self._poolname and self._poolurl are present with ``

        if <pre-requisit not met>: return True
        if super().setup(): return True

        # super().setup() has done its things by now.
        <do setup>
        return False
``
        returns: True if not both  self._poolname and self._poolurl are present.

        """

        if super().setup():
            return True
        # new ##

        self._dTags = dict()

        return False

    def getTags(self, urn=None, datatype=None, sn=None, **kwds):
        """ 
        Get all of the tags that map to a given URN or a pair of data type and serial number.

        Get all known tags if input arenot specified.

        If datatype and sn are given, use them and ignore urn.
        """

        urn, datatype, sn = self.get_missing(
            urn=urn, datatype=datatype, sn=sn)
        if urn is None:
            return self._dTags.keys()

        # new ###
        # assert self._urns[urn]['tags'] == self._dTypes[datatype]['sn'][sn]['tags']
        # return self._urns[urn]['tags']

        p = self._dTypes[datatype]['sn'][sn].get('tags', set())

        return p

    get_missing = get_missing

    def getTagUrnMap(self):
        """
        Get the full tag->urn mappings.

        """
        # new ###
        return self._dTags

        # return zip(self._tags.keys(), map(lambda v: v['urns'], self._value()))

    def getUrn(self, tag):
        """
        Gets the URNs corresponding to the given tag.

        Returns an empty list if `tag` is not `None` and does not exist.
        curl -X GET "http://123.56.102.90:31702/csdb/v1/storage/info?urns=urn%3Apoolbs%3A20211018%3A1" -H "accept: */*"

        """
        if 0:
            if tag not in self._tags:
                return []
        if tag not in self._dTags:
            return []
        # new ###
        if 0:
            assert list(self._tags) == list(self._dTags)
            assert list(self._tags[tag]['urns']) == list(':'.join(
                ['urn', self._poolname, cl, sn]) for cl in self._dTags[tag] for sn in self._dTags[tag][cl])
            return self._tags[tag]['urns']
        # datatype:[sn] -> [urn:poolname:datatype:sn]
        # return ['urn:%s:%s' % (self._poolname, t) for t in self._dTags[tag]]
        t = self._dTags[tag]
        pn = self._poolname
        return list(':'.join(['urn', pn, cl, sn]) for cl in t for sn in t[cl])

    def getUrnObject(self, tag):
        """
        Gets the URNobjects corresponding to the given tag.
        Returns an empty list if `tag` does not exist.
        """

        if 0:
            assert list(self._tags[tag]['urns']) == list(self._dTags[tag])
            return [Urn(x) for x in self._tags[tag]['urns']]
        return [Urn(x) for x in self._dTags[tag]]

    def getAllUrns(self):
        """ Returns a list of all URNs in the pool."""
        res = []
        poolname = self.poolname
        for cls, v in self._dTypes.items():
            res.extend(f'urn:{poolname}:{cls}:{sn}' for sn in v['sn'])
        return res

    def removekey(self, key, thecontainer, thename, cross_ref_map, othername):
        """
        Remove the given key from `the map` and the counterpart key in the correponding `cross_referencing map`.
        """
        vals = thecontainer.pop(key, [])
        # remove all items whose v is key in cross_ref_map
        for val in vals[othername]:
            cross_ref_map[val][thename].remove(key)
            # if we have just removed the last key, remove the empty dict
            if len(cross_ref_map[val][thename]) == 0:
                cross_ref_map[val].pop(thename)
                # if this caused the cross_ref_map[val] to be empty, remove the empty dict
                if len(cross_ref_map[val]) == 0:
                    cross_ref_map.pop(val)

    def removeTag(self, tag, **kwds):
        """
        Remove the given tag from the H/K maps.

        """

        # new ##
        if tag not in self._dTags:
            logger.debug('Tag "{tag}" not found in pool {self._poolname}.')
            return 0
        clsn_sns = self._dTags.pop(tag)
        # {datatype:[sn0, sn1..]}
        for datatype, sns in clsn_sns.items():
            for sn in sns:
                # clear the tag from dTypes
                sn = int(sn)
                ts = self._dTypes[datatype]['sn'][sn]['tags']
                if tag in ts:
                    ts.remove(tag)
                else:
                    logger.warning('tag %s missing from %s:%s:%s.' %
                                   (tag, self._poolname, datatype, sn))
                # Do not remove in the for sn .. loop, or the next tag
                # may complain no sn
                if len(ts) == 0:
                    del ts
        # self.removekey(tag, self._tags, 'tags', self._urns, 'urns')
        # new ##
        # assert list(self._tags) == list(self._dTags)

        return 0

    def removeUrn(self, urn=None, datatype=None, sn=None):
        """
        Remove the given urn (or a pair of data type and serial number) from the tag and urn maps.

        Only changes maps in memory, not to write on disk here.
        """
        u, datatype, sn = self.get_missing(
            urn=urn, datatype=datatype, sn=sn,
            no_check=True)
        # new ##
        from .productpool import ProductPool
        dats, sns, alist = ProductPool.vectorize(datatype, sn)
        for d, s in zip(dats, sns):
            if not hasattr(self, '_dTypes') or d not in self._dTypes:
                msg = f'{d} not found on server.'
                if not self.ignore_error_when_delete:
                    raise ValueError(msg)
                else:
                    logger.debug(msg)

            _snd = self._dTypes[d]['sn']
            if s not in _snd:
                msg = f'{s} not found in pool {self.getId()}.'
                if not self.ignore_error_when_delete:
                    raise IndexError(msg)
                else:
                    logger.debug(msg)
                    continue
            if 'tags' in _snd[s]:
                for tag in _snd[s]['tags']:
                    if tag in self._dTags:
                        # remove sn from datatype
                        self._dTags[tag][d].remove(str(s))
                        if len(self._dTags[tag][d]) == 0:
                            del self._dTags[tag][d]
                            if len(self._dTags[tag]) == 0:
                                del self._dTags[tag]
                    else:
                        logger.warning('tag %s missing from %s.' %
                                       (tag, self._poolname))
                else:
                    if 0:
                        logger.warning('tag %s missing from %s:%s:%s.' %
                                       (tag, self._poolname, d, s))
            _snd.pop(s)
            if len(_snd) == 0:
                pass  # del self._dTypes[d]
            # /new ##

            # self.removekey(u, self._urns, 'urns', self._tags, 'tags')
            # new ##
            # assert s not in self._dTypes[d]['sn']

    def setTag(self, tag, urn=None, datatype=None, sn=None):
        """
        Sets the specified tag to the given URN or a pair of data type and serial number.

        """
        u, datatype, sn = self.get_missing(
            urn=urn, datatype=datatype, sn=sn, no_check=True)

        if 0:
            self._urns[u]['tags'].append(tag)

            if tag in self._tags:
                self._tags[tag]['urns'].append(u)
            else:
                self._tags[tag] = {'urns': [u]}

        # new ###
        add_tag_datatype_sn(tag, datatype, sn,
                            dTypes=self._dTypes, dTags=self._dTags)
        if 0:
            snt = self._dTypes[datatype]['sn'][sn]['tags']
            if tag not in snt:
                snt.append(tag)
            # dTags saves datatype:sn
            _, typ, sn = tuple(u.rsplit(':', 2))
            if tag not in self._dTags:
                self._dTags[tag] = {}
            t = self._dTags[tag]
            if typ not in t:
                t[typ] = [sn]
            else:
                t[typ].append(sn)

    def tagExists(self, tag):
        """
        Tests if a tag exists.

        """
        # new ##
        if 0:
            assert (tag in self._dTags) == (tag in self._tags)
            return tag in self._tags
        return tag in self._dTags
