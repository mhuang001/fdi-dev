# -*- coding: utf-8 -*-

from fdi.dataset.odict import ODict
from fdi.dataset.dataset import TableDataset, IndexedTableDataset
from fdi.dataset.indexed import Indexed
import random
from operator import itemgetter
import gc
import timeit

import string
from timethese import cmpthese, pprint_cmp, timethese

loop = 5
rpt = 2
N = 100000


gc.collect()
gc.disable()

t = [random.randrange(N) for i in range(N)]

print('1D', N)


def none1():
    [p for p in t]


yl = [random.randrange(N) for i in range(N)]


def list1():
    [yl[p] for p in t]


yd = dict((i, random.randrange(N)) for i in range(N))


def dict1():
    [yd[p] for p in t]


yo = ODict((i, random.randrange(N)) for i in range(N))


def odict1():
    [yo[p] for p in t]


yo = ODict((i, random.randrange(N)) for i in range(N))
yod = yo.data


def od_data1():
    [yod[p] for p in t]


tdata = [[random.randrange(N) for i in range(N)]]
# , [random.randrange(N) for i in range(N)]]
tab = TableDataset(data=tdata)
tab_map = tab.list


def Tab1():
    tab.getRow(t)


def Tab_m1():
    [tuple(c[p] for c in tab_map) for p in t]


idx = Indexed(indexPattern=[0])
idx.data = [t]  # value look-up needs to confine the value set
idx.updateToc()


def Ind1():
    [idx.vLookUp(p, return_index=1) for p in t]


def Ind_m1():
    idx.vLookUp(t, return_index=1, multiple=True)


it = IndexedTableDataset(data=tdata)
it.indexPattern = [0]
it.data = [t]
it.updateToc()


def IndTab1():
    [it.vLookUp(p, return_index=1) for p in t]


def IndT_m1():
    it.vLookUp(t, return_index=1, multiple=True)


res = cmpthese(loop,
               [none1, list1, dict1, odict1, od_data1,
                Tab1, Tab_m1, Ind1, Ind_m1,
                IndTab1, IndT_m1],
               repeat=rpt)

print(pprint_cmp(res))

del yl, yd, yo, yod, t, tdata, tab
#############

gc.collect()
gc.disable()

m = 1000
n = 1024
N2 = m*n
print('\n2D', N2, m, n)

t2 = [(random.randrange(m), random.randrange(n)) for i in range(N2)]


def none2():
    [1 for p, q in t2]


yl2 = [[random.randrange(N) for i in range(n)] for j in range(m)]


def list2():
    [yl2[p][q] for p, q in t2]


yd2 = dict(((i, j), random.randrange(N)) for i in range(m) for j in range(n))


def dict2():
    [yd2[p] for p in t2]


yo2 = ODict(((i, j), random.randrange(N)) for i in range(m) for j in range(n))


def odict2():
    [yo2[p] for p in t2]


idx2 = Indexed(indexPattern=[0, 1])
idx2.data = list(zip(*t2))
idx2.updateToc()


def Indexed2():
    [idx2.vLookUp(p) for p in t2]


def Ind_m2():
    idx2.vLookUp(t2, multiple=1)


res = cmpthese(1,
               [none2, list2, dict2, odict2,
                Indexed2, Ind_m2],
               repeat=rpt)

print(pprint_cmp(res))

gc.collect()
gc.disable()

LoL = [[c1, c2]
       for c1, c2 in zip(string.ascii_lowercase, string.ascii_uppercase)] * (N//25)


def lc_d(item='d'):
    return item in [i for sub in LoL for i in sub]


def ge_d(item='d'):
    return item in (y for x in LoL for y in x)


def any_lc_d(item='d'):
    return any(item in x for x in LoL)


def any_gc_d(item='d'):
    return any([item in x for x in LoL])


def lc_z(item='z'):
    return item in [i for sub in LoL for i in sub]


def ge_z(item='z'):
    return item in (y for x in LoL for y in x)


def any_lc_z(item='z'):
    return any(item in x for x in LoL)


def any_gc_z(item='z'):
    return any([item in x for x in LoL])


res = cmpthese(loop,
               [lc_d, ge_d, any_gc_d, any_gc_z, any_lc_d, any_lc_z, lc_z, ge_z],
               repeat=rpt)

print(pprint_cmp(res))

exit()

# https://stackoverflow.com/a/11922913/13472124
seq_of_tups = (('a', 1), ('b', 2), ('c', 3))


def d124a(): G


'a' in map(itemgetter(0), seq_of_tups)


def d124b():
    'a' in (x[0] for x in seq_of_tups)


def d124c():
    any(x == 'a' for x, y in seq_of_tups)


def d124d():
    any(x[0] == 'a' for x in seq_of_tups)


print(pprint_cmp(cmpthese(10000, [d124a, d124b, d124c, d124d], repeat=3)))
