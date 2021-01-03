# -*- coding: utf-8 -*-

import time
import timeit

loop = 1
rpt = 1
N = 1000000

print('1D', N)

print('none')
t0 = time.time()
t = timeit.Timer('[p for p in t]',
                 setup='import random; gc.enable(); N=%d; t, y = [random.randrange(N) for i in range(N)], [random.random() for i in range(N)]' % N)
t1 = t.repeat(rpt, number=loop)
print(t1, 'setup', time.time()-t0-t1[0])

print('list')
t0 = time.time()
t = timeit.Timer('[y[p] for p in t]',
                 setup='import random; gc.enable(); N=%d; t, y = [random.randrange(N) for i in range(N)], [random.random() for i in range(N)]' % N)
t1 = t.repeat(rpt, number=loop)
print(t1, 'setup', time.time()-t0-t1[0])

print('dict')
t0 = time.time()
t = timeit.Timer('for p in t: y[p]',
                 setup='import random; gc.enable(); N=%d; t, y = [random.randrange(N) for i in range(N)], dict((i, random.random()) for i in range(N))' % N)
t1 = t.repeat(rpt, number=loop)
print(t1, 'setup', time.time()-t0-t1[0])

print('odict')
t0 = time.time()
t = timeit.Timer('for p in t: a[p]',
                 setup='import random; from fdi.dataset.odict import ODict; gc.enable(); N= %d; t, y = [random.randrange(N) for i in range(N)], ODict((i, random.random()) for i in range(N));a=y.data' % (N))
t1 = t.repeat(rpt, number=loop)
print(t1, 'setup', time.time()-t0-t1[0])

print('TableDataset')
t0 = time.time()
t = timeit.Timer('for p in t: a.getRow(p)',
                 setup='import random; from fdi.dataset.dataset import TableDataset; gc.enable(); N= %d; t, y = [random.randrange(N) for i in range(N)], [list(random.random() for i in range(N))];a=TableDataset(data=y)' % (N))
t1 = t.repeat(rpt, number=loop)
print(t1, 'setup', time.time()-t0-t1[0])

#############

m = 1000
n = N//m
print('\n2D', N, m, n)

print('none')
t0 = time.time()
t = timeit.Timer('for p,q in t: pass',
                 setup='import random; gc.enable(); N, m, n=%d, %d, %d; t, y = [(random.randrange(m), random.randrange(n)) for i in range(N)], [[random.random() for i in range(n)] for j in range(m)]' % (N, m, n))
t1 = t.repeat(rpt, number=loop)
print(t1, 'setup', time.time()-t0-t1[0])


print('list')
t0 = time.time()
t = timeit.Timer('for p,q in t: y[p][q]',
                 setup='import random; gc.enable(); N, m, n=%d, %d, %d; t, y = [(random.randrange(m), random.randrange(n)) for i in range(N)], [[random.random() for i in range(n)] for j in range(m)]' % (N, m, n))
t1 = t.repeat(rpt, number=loop)
print(t1, 'setup', time.time()-t0-t1[0])

print('dict')
t0 = time.time()
t = timeit.Timer('for p in t: y[p]',
                 setup='import random; gc.enable(); N, m, n=%d, %d, %d; t, y = [(random.randrange(m), random.randrange(n)) for i in range(N)], dict(((i, j), random.random()) for i in range(m) for j in range(n))' % (N, m, n))
t1 = t.repeat(rpt, number=loop)
print(t1, 'setup', time.time()-t0-t1[0])

print('odict')
t0 = time.time()
t = timeit.Timer('for p in t: a[p]',
                 setup='import random; from fdi.dataset.odict import ODict; gc.enable(); N, m, n=%d, %d, %d; t, y = [(random.randrange(m), random.randrange(n)) for i in range(N)], ODict(((i, j), random.random()) for i in range(m) for j in range(n));a=y.data' % (N, m, n))
t1 = t.repeat(rpt, number=loop)
print(t1, 'setup', time.time()-t0-t1[0])

print('TableDataset')
t0 = time.time()
t = timeit.Timer('for p in t: a.getRow(p)',
                 setup='import random; from fdi.dataset.dataset import TableDataset; gc.enable(); N, m, n=%d, %d, %d; t, y = [(random.randrange(m), random.randrange(n)) for i in range(N)], [((i, list( random.random() for i in range(m) for j in range(n));a=TableDataset(data=y)' % (N, m, n))
t1 = t.repeat(rpt, number=loop)
print(t1, 'setup', time.time()-t0-t1[0])
