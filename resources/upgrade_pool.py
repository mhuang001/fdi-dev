#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fdi.pal.localpool import LocalPool
from fdi.pal.productstorage import ProductStorage
from fdi.pal.urn import makeUrn
from fdi.utils.common import lls

import os
import sys
import argparse
import itertools
import pprint
import logging

# create logger
logger = logging.getLogger(__file__)
logging.basicConfig(stream=sys.stdout,
                    format='%(asctime)s -%(levelname)4s'
                           ' -[%(filename)s:%(lineno)3s'
                           ' -%(funcName)10s()] - %(message)s',
                    datefmt="%Y%m%d %H:%M:%S")

if __name__ == '__main__':

    # schema version
    version = '1'

    # Get input file name etc. from command line. defaut 'Product.yml'
    dry_run = False

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--dir_of_pool", type=str,
                        default='.', help="Where to find the pool.")
    parser.add_argument("-v", "--verbose", action='store_true',
                        default=False, help="Set debugging info.")

    args = parser.parse_args()
    if args.verbose:
        print(args)
    lv = logging.DEBUG if args.verbose else logging.INFO

    logger.setLevel(lv)

    poolname = args.dir_of_pool.strip('/').split('/')[-1]
    poolpath = os.path.abspath(args.dir_of_pool)
    poolurl = 'file://' + poolpath
    pstore = ProductStorage(poolname, poolurl)
    pool = pstore.getPool(pstore.getWritablePool())

    print('Upgrade pool ===== %s =====.' % poolname)

    classes, tags, urns, dTypes, dTags = tuple(pool.readHK().values())
    # consistency check
    ulist, tlist, ut, mlist, rlist = [], [], [], [], []
    dTypes, dTags = {}, {}
    for cl, cldata in classes.items():
        dTypes[cl] = {'currentSN': cldata['currentSN'],
                      'sn': {}}
        for sn in cldata['sn']:
            urn = makeUrn(poolname, cl, sn)
            ulist.append(urn)
            assert urn in urns
            # populate dTypes
            snd = {}
            dTypes[cl]['sn'][sn] = snd
            if 'tags' in urns[urn]:
                for tag in urns[urn]['tags']:
                    assert tag in tags
                    assert urn in tags[tag]['urns']
                    if urn not in ut:
                        # urns w/ a tag
                        ut.append(urn)
                    tlist.append(tag)
                    if 'tags' not in snd:
                        snd['tags'] = []
                    snd['tags'].append(tag)
                    # populate dTags
                    if tag not in dTags:
                        t = dTags[tag] = {}
                    if cl not in t:
                        c = t[cl] = []
                    c.append(str(sn))
            if 'meta' in urns[urn]:
                snd['meta'] = urns[urn]['meta']
                mlist.append(urn)
            if 'refcnt' in urns[urn]:
                snd['meta'] = urns[urn]['refcnt']
                rlist.append(urn)
    assert set(ulist) == set(urns.keys())
    assert set(tlist) == set(tags.keys())
    print("Consistency of HK data in pool %s checked.\n%d URNs %s\n%d Tags %s" %
          (poolname, len(ulist), str(ulist) if args.verbose else '', len(tlist), str(tlist) if args.verbose else ''))
    print('%d meta sizes. %d ref counts: %s' %
          (len(mlist), len(rlist), lls(rlist) if args.verbose else ''))
    clsns = (cl+':'+str(sn) for cl, dat in dTypes.items()
             for sn in dat['sn'])
    assert set(ulist) == set('urn:'+poolname+':'+x for x in clsns)
    print('urns in dTypes checked')
    assert set(tlist) == set(dTags.keys())
    tclsns = (cl+':'+str(sn) for cl, dat in dTypes.items()
              for sn, snd in dat['sn'].items() if snd.get('tags'))
    setc = set('urn:'+poolname+':'+x for x in tclsns)
    assert set(ut) == setc, str(set(ulist)) + ' ' + str(setc)
    print('urns in dTags checked')

    if args.verbose:
        print(dTypes)
        print(dTags)
    # only update the new versions
    pool._dTypes = dTypes
    pool._dTags = dTags

    pool.writeHK(all_versions=False)
    print('Written '+poolname)
