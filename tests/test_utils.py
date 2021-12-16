# -*- coding: utf-8 -*-
from fdi.dataset.arraydataset import ArrayDataset,Column as aCol
from fdi.dataset.tabledataset import TableDataset
from fdi.dataset.dataset import CompositeDataset
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.dateparameter import DateParameter
from fdi.dataset.stringparameter import StringParameter
from fdi.dataset.dataset import Dataset
from fdi.dataset.numericparameter import NumericParameter,BooleanParameter
from fdi.utils.fits_kw import FITS_KEYWORDS, getFitsKw
from fdi.utils.leapseconds import utc_to_tai, tai_to_utc, dTAI_UTC_from_utc, _fallback
from fdi.dataset.eq import deepcmp
from fdi.dataset.metadata import make_jsonable
from fdi.dataset.finetime import FineTime
from fdi.dataset.datatypes import Vector, Quaternion
from fdi.dataset.deserialize import Class_Look_Up, serialize_args, deserialize_args
from fdi.pal.urn import Urn
from fdi.pal.productref import ProductRef
from fdi.utils.checkjson import checkjson
from fdi.utils.loadfiles import loadcsv
from fdi.utils import moduleloader
from fdi.utils.common import fullname
from fdi.utils.options import opt
from fdi.utils.fetch import fetch
from fdi.utils.loadfiles import loadMedia
from fdi.utils.tofits import toFits
from fdi.utils.tofits import fits_dataset

from astropy.io import fits

import traceback
import copy
from datetime import timezone, timedelta, datetime
import sys
import os
import io
import hashlib
import os.path
import pytest
import numpy as np

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

if __name__ == '__main__' and __package__ == 'tests':
    # run by python -m tests.test_dataset
    pass
else:
    # run by pytest

    # This is to be able to test w/ or w/o installing the package
    # https://docs.python-guide.org/writing/structure/

    from pycontext import fdi

    from logdict import logdict
    import logging
    import logging.config

    # create logger
    logging.config.dictConfig(logdict)
    logger = logging.getLogger()
    logger.debug('%s logging level %d' %
                 (__name__, logger.getEffectiveLevel()))

    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("filelock").setLevel(logging.WARN)

def test_fits_dataset():
    ima=ArrayDataset(data=[[1,2,3,4],[5,6,7,8]], description='a')
    imb=ArrayDataset(data=[[1,2,3,4],[5,6,7,8],[1,2,3,4],[5,6,7,8]], description='b')
    #im=[[1,2,3,4],[5,6,7,8]]
    
    hdul = fits.HDUList()
    hdul.append(fits.PrimaryHDU())
    data=[ima,imb]
    u=fits_dataset(hdul,data)
    assert issubclass(u.__class__, fits.HDUList)    
    assert len(u) == len(data)+1

def test_tab_fits():
    d= {'col1': aCol(data=[1, 4.4, 5.4E3], unit='eV'),
              'col2': aCol(data=[0, 43, 2E3], unit='cnt')}
    d['col1'].type='d'
    d['col2'].type='i'
    ds=TableDataset(data=d)
    data=[ds]
    #__import__('pdb').set_trace()
    u=toFits(data)
    assert issubclass(u.__class__, fits.HDUList)
    print('test_tab_fits',u[0])
    assert u[1].columns['col1'].unit == 'eV'
    assert u[1].data[0][0] == str(d['col1'].data[0])
    assert u[1].data[1][1] == str(d['col2'].data[1])
@pytest.fixture(scope='module')
def makecom():
    a1 = [768, 4.4, 5.4E3]
    a2 = 'ev'
    a3 = 'arraydset 1'
    a4 = ArrayDataset(data=a1, unit=a2, description=a3)
    a5, a6, a7 = [[1.09, 289], [3455, 564]], 'count', 'arraydset 2'
    #a8 = ArrayDataset(data=a5, unit=a6, description=a7)
    d = {'col1': aCol(data=[1, 4.4, 5.4E3], unit='eV'),
              'col2': aCol(data=[0, -43, 2E3], unit='cnt')}
    d['col1'].typecode='d'
    d['col2'].typecode='i'
    a8=TableDataset(data=d)
    v = CompositeDataset()
    a9 = 'dataset 1'
    a10 = 'dataset 2'
    v.set(a9, a4)
    v.set(a10, a8)
    assert v[a9]==a4
    a11 = 'm1'
    a12 = NumericParameter(description='a different param in metadata',
                           value=2.3, unit='sec')
    v.meta[a11] = a12
    return v
def test_com_fits(makecom):
    v=makecom
    data=[v]
    #__import__('pdb').set_trace()
    u=toFits(data)
    print(u,len(u))
    assert u[2].data[0]==v['dataset 1'].data[0]
    assert u[2].shape==v['dataset 1'].shape
    assert u[3].data['col1'][1]==v['dataset 2']['col1'][1]
    assert u[3].data.dtype[0]=='<f8'
    
"""
    "A": "B",  # ASCII char
    "L": "B",  # boolean
    "X": "H",  # unsigned short
    "B": "B",  # unsigned char
    "S": "b",  # signed char
    "I": "h",  # signed short
    "U": "H",  # unsigned short
    "J": "i",  # signed integer
    "V": "I",  # unsigned integer
    "K": "l",  # signed long
    "E": "d",  # double
    "D": "d",  # double
    "C": "c",  # complex
    "M": "c"  # complex
"""
tcode={'b': np.bool,            #Boolean
      'i8': np.int8,            #8-bit signed integer
       'i16': np.int16,         #16-bit signed integer
       'i32': np.int32,         #32-bit signed integer
       'i64': np.int64,         #64-bit signed integer
       'u8': np.uint8,          #8-bit unsigned integer
       'u16': np.uint16,        #16-bit unsigned integer
       'u32': np.uint32,        #32-bit unsigned integer
       'u64': np.uint64,        #64-bit unsigned integer
       'f16': np.float16,       #16-bit floating point number
       'f32': np.float32,       #32-bit floating point number
       'f64': np.float64,       #64-bit floating point number
       'c64': np.complex64,     #64-bit complex number
       'c128': np.complex128    #128-bit complex number
}

def test_toFits_metadata(makecom):
    for ds in [ArrayDataset,TableDataset,CompositeDataset]:
        if issubclass(ds, ArrayDataset):
            ima=ds(data=[[1,2,3,4],[5,6,7,8]], description='a')
        elif issubclass(ds,TableDataset):
            d= {'col1': aCol(data=[1, 4.4, 5.4E3], unit='eV'),
              'col2': aCol(data=[0, -43, 2E3], unit='cnt')}
            d['col1'].typecode='d'
            d['col2'].typecode='i'
            ima=ds(data=d)
        elif issubclass(ds, CompositeDataset):
            #__import__('pdb').set_trace()
            ima=makecom
        else:
            assert False
        ima.meta['datetime']=DateParameter(
        '2023-01-23T12:34:56.789012',description='date keyword')
        ima.meta['quat']=NumericParameter([0.0,1.1,2.4,3.5],description='q')
        ima.meta['float']=NumericParameter(1.234,description='float keyword')
        ima.meta['integer']=NumericParameter(1234,description='integer keyword')
        ima.meta['string_test']=StringParameter('abc',description=' string keyword')
        ima.meta['boolean_test']=BooleanParameter(True,description=' boolean keyword')
        imb=ArrayDataset(data=[[1,2,3,4],[5,6,7,8],[1,2,3,4],[5,6,7,8]], description='b')
        
        
        data=[ima]
        u=toFits(data)
        assert issubclass(u.__class__, fits.HDUList)
        #assert len(u) == len(data)+1
        print("-----",u[0].header)
        w=u[1]
        print(w.header)
        assert w.header['DATETIME']=='2023-01-23T12:34:56.789012'
        assert w.header['QUAT0']==0.0
        assert w.header['QUAT1']==1.1
        assert w.header['QUAT2']==2.4
        assert w.header['QUAT3']==3.5
        assert w.header['FLOAT']==1.234
        assert w.header['INTEGER']==1234
        assert w.header['STRING_T']=='abc'
        assert w.header['BOOLEAN_']=='T'
        
        if issubclass(ds, ArrayDataset):
            assert w.header['NAXIS1']==len(ima.data[0])
            assert w.header['NAXIS2']==len(ima.data)
            assert w.header['NAXIS']==len(ima.shape)
            assert w.data[0][0] == ima[0][0]
            assert w.data[1][1] == ima[1][1]
        elif issubclass(ds,TableDataset):
        
            assert w.data[0][0] == d['col1'].data[0]
            assert w.data[1][1] == d['col2'].data[1]
        elif issubclass(ds,CompositeDataset):
            pass
def test_prd_fits(makecom):
    c=makecom
    p=BaseProduct('abc')
    p['com']=c
    p.meta['creationDate']=DateParameter(
        '2023-01-23T12:34:56.789012',description='date keyword')
    v=toFits(p)
    
    assert v[2].data[0]==c['dataset 1'].data[0]
    assert v[0].header['DESC']=='abc'
    assert v[0].header['TYPE']=='BaseProduct'
    assert v[0].header['DATE']=='2023-01-23T12:34:56.789012'
    v=toFits(p, '/tmp/test.fits',overwrite=1)
    f=fits.open('/tmp/test.fits')
    f.close()
    assert f[0].header==v[0].header
    ###test stream
    #__import__('pdb').set_trace()
    f=open('/tmp/test.fits','wb+')
    stream=toFits(p, '')
    f.write(stream)
    f.close()
    f=fits.open('/tmp/test.fits')
    f.close()
    assert f[0].header==v[0].header
    del f
    
def test_get_demo_product(demo_product):
    v, related = demo_product
    assert v['Browse'].data[1:4] == b'PNG'
    # print(v.yaml())
    p = v.getDefault()
    assert p == v['results']
    aref = ProductRef(related)
    v.refs['a'] = aref
    r0 = v.refs
    p['dset'] = 'foo'
    # refs is always the last
    assert list(v.keys())[-1] == 'refs'
    assert r0 == v.refs
    # existing key
    p['dset'] = 'foo'
    assert list(v.keys())[-1] == 'refs'
    assert r0 == v.refs
    checkjson(v, dbg=0)
    checkgeneral(v)


def checkgeneral(v):
    # can always add attributes
    t = 'random'
    v.testattr = t
    assert v.testattr == t
    try:
        m = v.notexists
    except AttributeError as e:
        assert str(e).split()[-1] == "'notexists'", traceback.print_exc()
    except:
        traceback.print_exc()
        assert false


def chk_sample_pd(p):
    v, s = fetch(["description"], p)
    assert v == p.description
    assert s == '.description'
    # metadatax
    with pytest.raises(KeyError):
        e = p.meta['extra']

    v, s = fetch(["meta", "speed"], p)
    assert v == p.meta['speed']
    assert s == '.meta["speed"]'
    # parameter
    v, s = fetch(["meta", "speed", "unit"], p)
    assert v == 'meter'
    assert v == p.meta['speed'].unit
    assert s == '.meta["speed"].unit'

    v, s = fetch(["meta", "speed", "value"], p)
    assert v == Vector((1.1, 2.2, 3.3))
    assert v == p.meta['speed'].value
    assert s == '.meta["speed"].value'
    v, s = fetch(["meta", "speed", "valid"], p)
    mkj = make_jsonable({(1, 22): 'normal', (30, 33): 'fast'})
    assert v == mkj
    assert v == make_jsonable(p.meta['speed'].valid)
    assert s == '.meta["speed"].valid'
    # TODO written is string
    # [[[1, 22], 'normal'], [[30, 33], 'fast']]
    v, s = fetch(["meta", "speed", "valid", 0, 1], p)
    assert v == 'normal'
    assert v == p.meta['speed'].valid[0][1]
    assert s == '.meta["speed"].valid[0][1]'
    #
    # validate execution
    v, s = fetch(["meta", "speed", "isValid", ], p)
    assert v == True
    assert v == p.meta['speed'].isValid()
    assert s == '.meta["speed"].isValid()'

    # datasets
    #
    v, s = fetch(["Environment Temperature", "unit"], p)
    assert v == 'C'
    assert v == p['Environment Temperature'].unit
    assert s == '["Environment Temperature"].unit'

    v, s = fetch(["Environment Temperature", "data"], p)
    assert v == [768, 767, 766, 4.4, 4.5, 4.6, 5.4E3]
    assert v == p['Environment Temperature'].data
    assert s == '["Environment Temperature"].data'

    # dataset has a parameter
    v, s = fetch(["Environment Temperature", "T0", "tai"], p)
    assert v == FineTime('2020-02-02T20:20:20.0202').tai

    # a 2D array dataset in compositedataset 'results'
    v, s = fetch(["results", 'calibration', "unit"], p)
    assert v == 'count'
    assert v == p['results']['calibration'].unit
    assert s == '["results"]["calibration"].unit'

    # data of a column in tabledataset within compositedataset
    v, s = fetch(["results", "Time_Energy_Pos", "Energy", "data"], p)
    t = [x * 1.0 for x in range(len(v))]
    assert v == [2 * x + 100 for x in t]
    assert v == p['results']['Time_Energy_Pos']['Energy'].data
    assert s == '["results"]["Time_Energy_Pos"]["Energy"].data'
    ys, s = fetch(["results", "Time_Energy_Pos", "y"], p)
    zs, s = fetch(["results", "Time_Energy_Pos", "z"], p)
    # y^2 + z^2 = 100 for all t
    assert all((y*y + z*z - 100) < 1e-5 for y, z in zip(ys.data, zs.data))


def test_fetch(demo_product):

    # simple nested structure
    v = {1: 2, 3: 4}
    u, s = fetch([3], v)
    assert u == 4
    assert s == '[3]'
    v = {'1': 2, 3: 4}
    u, s = fetch(['1'], v)
    assert u == 2
    assert s == '["1"]'
    v.update(d={'k': 99})
    u, s = fetch(['d', 'k'], v)
    assert u == 99
    assert s == '["d"]["k"]'
    # 3 levels
    v = [4, v,  5]
    w = copy.deepcopy(v)
    u, s = fetch([0], w)
    assert u == 4
    u, s = fetch([2], w)
    assert u == 5
    assert s == '[2]'
    u, s = fetch([1, 'd', 'k'], w)
    assert u == 99
    assert s == '[1]["d"]["k"]'

    # path is str
    assert fetch([2], w) == fetch('2', w)
    assert fetch([1, 'd', 'k'], w) == fetch(
        '1/d/k', w) == fetch('1.d.k', w, sep='.')
    assert fetch('/1/d/k ', w) == fetch('1.d.k', w, sep='.')
    assert fetch(' ', w, re='asd') == (w, 'asd')

    # objects

    class al(list):
        ala = 0
        @staticmethod
        def alb(): pass

        def alf(self, a, b=9):
            return a, b

        def __init__(self, *a, i=[8], **k):
            super().__init__(*a, **k)
            self.ald = i
        alc = {3: 4}
        ale = [99, 88]

    # init
    v = al(i=[1, 2])
    u, s = fetch(['ald'], v)
    assert u == [1, 2]
    assert s == '.ald'

    # class property list
    u, s = fetch(['ale', 1], v)
    assert u == 88
    assert s == '.ale[1]'

    # class property dict
    u, s = fetch(['alc', 3], v)
    assert u == 4
    assert s == '.alc[3]'

    # method
    u, s = fetch(['alb'], v)
    assert u is None
    assert s == '.alb()'

    # method w/ positional arg
    u, s = fetch(['alf__4.4'], v)
    assert u == (4.4, 9)
    assert s == '.alf(4.4)'

    # method w/ positional and keyword args
    allargs = serialize_args(4.4, [{"w": 77}, 65], not_quoted=True)
    assert allargs == '4.4__{"apiargs": [[{\"w\": 77}, 65]]}'
    u, s = fetch(['alf__' + allargs], v)
    assert u == (4.4, [{"w": 77}, 65])
    assert s == ".alf(4.4, [{'w': 77}, 65])"

    # method/function result
    u, s = fetch(['alf__' + allargs, 1, 0, 'w'], v)
    assert u == 77
    assert s == ".alf(4.4, [{'w': 77}, 65])[1][0][\"w\"]"

    class ad(dict):
        ada = 'p'
        adb = al([0, 6])

    v = ad(z=5, x=['b', 'n', {'m': 'j'}])
    v.ade = 'adee'

    u, s = fetch(['ada'], v)
    assert u == 'p'
    assert s == '.ada'

    u, s = fetch(['adb', 'ald', 0], v)
    assert u == 8
    assert s == '.adb.ald[0]'

    u, s = fetch(['x', 2, 'm'], v)
    assert u == 'j'
    assert s == '["x"][2]["m"]'

    # products
    p, r = demo_product
    chk_sample_pd(p)


def test_Fits_Kw():
    # Fits to Parameter name
    assert FITS_KEYWORDS['DATASUM'] == 'checksumData'
    assert FITS_KEYWORDS['DESC'] == 'description'
    assert FITS_KEYWORDS['CUNIT'] == 'cunit'
    assert getFitsKw('checksumData') == 'DATASUM'
    assert getFitsKw('description') == 'DESC'
    assert getFitsKw('cunit01') == 'CUNIT01'
    assert getFitsKw('description01234') == 'DESC34'
    # with pytest.raises(ValueError):
    assert getFitsKw('checksumData0123', 3) == 'DATAS123'
    assert getFitsKw('checksumData0123', 2) == 'DATASU23'
    with pytest.raises(TypeError):
        assert getFitsKw('foo0123', 5, (('foo', 'BAR'))) == 'BAR0123'
    assert getFitsKw('foo0123', 5, (('foo', 'BAR'),)) == 'BAR0123'


def test_loadcsv():
    csvf = '/tmp/fditest/testloadcsv.csv'
    a = 'as if ...'
    with open(csvf, 'rw') as f:
        f.write(a)
    v = loadcsv(csvf, ' ')
    assert v[0] == ('col1', ['as'], '')
    assert v[1] == ('col2', ['if'], '')
    assert v[2] == ('col3', ['...'], '')

    a = ' \t\n'+a
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ' ')
    assert v[0] == ('col1', ['as'], '')
    assert v[1] == ('col2', ['if'], '')
    assert v[2] == ('col3', ['...'], '')

    # blank line skipped
    a = a + '\n1 2. 3e3'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ' ')
    assert v[0] == ('col1', ['as', 1.0], '')
    assert v[1] == ('col2', ['if', 2.0], '')
    assert v[2] == ('col3', ['...', 3000.], '')

    # first line as header

    v = loadcsv(csvf, ' ', header=1)
    assert v[0] == ('as', [1.0], '')
    assert v[1] == ('if', [2.0], '')
    assert v[2] == ('...', [3000.], '')

    # a mixed line added. delimiter changed to ','
    a = 'as, if, ...\nm, 0.2,ev\n1, 2., 3e3'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ',', header=1)
    assert v[0] == ('as', ['m', 1.0], '')
    assert v[1] == ('if', ['0.2', 2.0], '')
    assert v[2] == ('...', ['ev', 3000.], '')

    # anothrt line added. two header lines requested -- second line taken as unit line
    a = 'as, if, ...\n A, B, R \n m, 0.2,ev\n1, 2., 3e3'
    with open(csvf, 'w') as f:
        f.write(a)
    v = loadcsv(csvf, ',', header=2)
    assert v[0] == ('as', ['m', 1.0], 'A')
    assert v[1] == ('if', ['0.2', 2.0], 'B')
    assert v[2] == ('...', ['ev', 3000.], 'R')


def test_loadMedia():
    fname = 'bug.gif'
    fname = os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                      'resources'), fname)
    image = loadMedia(fname, 'image/gif')
    ho = hashlib.md5()
    ho.update(image.data)
    md5 = ho.hexdigest()
    assert md5 == '57bbbd6f8cdeafe6dc617f8969448e3b'


def test_moduleloader():

    moduleloader.main(ipath=os.path.abspath('tests'))


def test_fullname():
    assert fullname(Urn()) == 'fdi.pal.urn.Urn'
    assert fullname(Urn) == 'fdi.pal.urn.Urn'
    assert fullname('l') == 'str'


def test_opt():
    options = [
        {'long': 'helpme', 'char': 'h', 'default': False,
         'description': 'print help'},
        {'long': 'name=', 'char': 'n', 'default': 'Boo',
         'description': 'name of ship'},
        {'long': 'verbose', 'char': 'v', 'default': True,
         'description': 'print info'}
    ]
    # no args. defaults returned
    out = opt(options, [])
    assert out[0]['result'] == False
    assert out[1]['result'] == 'Boo'
    assert out[2]['result'] == True

    assert options[1]['long'] == 'name='

    # options given in short format
    out = opt(options, ['exe', '-h', '-n Awk', '-v'])
    assert out[0]['result'] == True
    # leading and trailing white spaces in args are removed
    assert out[1]['result'] == 'Awk'
    # the switch always results in True!
    assert out[2]['result'] == True

    # options given in long format
    out = opt(options, ['exe', '--helpme', '--name=Awk', '--verbose'])
    assert out[0]['result'] == True
    assert out[1]['result'] == 'Awk'
    # the switch always results in True!
    assert out[2]['result'] == True

    # type of result is determines by that of the default
    options[0]['default'] = 0
    out = opt(options, ['exe', '--helpme', '--name=Awk', '--verbose'])
    assert out[0]['result'] == 1

    # unplanned option and '--help' get exception and exits
    try:
        out = opt(options, ['exe', '--helpme', '--name=Awk', '-y'])
    except SystemExit:
        pass
    else:
        assert 0, 'failed to exit.'

    try:
        h = copy.copy(options)
        h[0]['long'] = 'help'
        out = opt(h, ['exe', '--help', '--name=Awk', '-v'])
    except SystemExit:
        pass
    else:
        assert 0, 'failed to exit.'


def check_conf(cfp, typ, getConfig):
    cfn = typ + 'local.py'
    cfp = os.path.expanduser(cfp)
    filec = os.path.join(cfp, cfn)
    os.system('rm -f ' + filec)
    conf = 'import os; %sconfig={"jk":98, "m":os.path.abspath(__file__)}' % typ
    with open(filec, 'w') as f:
        f.write(conf)
    # check conf file directory
    w = getConfig(conf=typ)
    assert w['jk'] == 98
    pfile = w['m']
    assert pfile.startswith(cfp)
    os.system('rm -f ' + filec)


def test_getConfig_init(getConfig):

    # no arg
    v = getConfig()
    from fdi.pns.config import pnsconfig
    # v is a superset
    assert all(n in v for n in pnsconfig)


def test_getConfig_noENV(getConfig):

    # non-default conf type
    typ = 'abc'
    # environment variable not set
    try:
        del os.environ['CONF_DIR']
    except:
        pass

    # default dir, there is  nothing
    # put mock in the default directory
    check_conf('~/.config', typ, getConfig)


def test_getConfig_conf(getConfig):

    # non-default conf type
    typ = 'abc'
    # specify directory
    cp = '/tmp'
    # environment variable
    os.environ['CONF_DIR_' + typ.upper()] = cp
    check_conf(cp, typ, getConfig)
    # non-existing. the file has been deleted by the check_conf in the last line
    w = getConfig(conf=typ)


def test_leapseconds():
    t0 = datetime(2019, 2, 19, 1, 2, 3, 456789, tzinfo=timezone.utc)
    assert dTAI_UTC_from_utc(t0) == timedelta(seconds=37)
    # the above just means ...
    assert utc_to_tai(t0) - t0 == timedelta(seconds=37)
    t1 = datetime(1972, 1, 1, 0, 0, 0, 000000, tzinfo=timezone.utc)
    assert dTAI_UTC_from_utc(t1) == timedelta(seconds=10)
    t2 = datetime(1970, 1, 1, 0, 0, 0, 000000, tzinfo=timezone.utc)
    # interpolation not implemented
    assert dTAI_UTC_from_utc(t2) == timedelta(seconds=4.213170)
    t3 = datetime(1968, 2, 1, 0, 0, 0, 000000, tzinfo=timezone.utc)
    assert dTAI_UTC_from_utc(t2) == timedelta(seconds=4.213170)
    t1958 = datetime(1958, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    assert dTAI_UTC_from_utc(t1958) == timedelta(seconds=0)
    # leap seconds is added on transition
    t4 = datetime(2017, 1, 1, 0, 0, 0, 000000, tzinfo=timezone.utc)
    assert utc_to_tai(t4) - utc_to_tai(t4 - timedelta(seconds=1)) == \
        timedelta(seconds=2)
    print(_fallback.cache_info())
