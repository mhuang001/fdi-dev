# -*- coding: utf-8 -*-

from fdi.utils.fits_kw import FITS_KEYWORDS, getFitsKw
from fdi.utils.tofits import is_Fits, toFits, fits_dataset, fits_header_list, write_to_file
from fdi.dataset.arraydataset import ArrayDataset, Column as aCol
from fdi.dataset.tabledataset import TableDataset
from fdi.dataset.dataset import CompositeDataset
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.dateparameter import DateParameter
from fdi.dataset.stringparameter import StringParameter
from fdi.dataset.product import Product
from fdi.dataset.numericparameter import NumericParameter, BooleanParameter
from fdi.dataset.metadata import MetaData
from fdi.pal.context import MapContext
from fdi.pal.productref import ProductRef

try:
    import numpy as np
    from astropy.io import fits
    FITS_INSTALLED = True
except ImportError:
    FITS_INSTALLED = False
    sys.exit(0)

import sys
import os
import pytest
import logging
# create logger
logger = logging.getLogger(__name__)
logger.debug('logging level %d' % (logger.getEffectiveLevel()))

if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False


def test_fits_err():
    ima = ArrayDataset(data=[[1, 2, 3, 4], [5, 6, 7, 8]], description='a')
    with pytest.raises(TypeError):
        v = toFits(MetaData())


def test_fits_dataset():
    ima = ArrayDataset(data=[[1, 2, 3, 4], [5, 6, 7, 8]], description='a')
    imb = ArrayDataset(data=[[1, 2, 3, 4], [5, 6, 7, 8], [
                       1, 2, 3, 4], [5, 6, 7, 8]], description='b')
    # im=[[1,2,3,4],[5,6,7,8]]

    hdul = fits.HDUList()
    hdul.append(fits.PrimaryHDU())
    data = [ima, imb]
    u = fits_dataset(hdul, data)
    assert issubclass(u.__class__, fits.HDUList)
    assert len(u) == len(data)+1
    assert list(u[1].data[0]) == [1, 2, 3, 4]

    assert u[1].header[getFitsKw('description')] == 'a'
    # w/ typecode
    ima = ArrayDataset(data=[[1, 2, 3, 4], [5, 6, 7, 8]], description='a', typecode='i')
    imb = ArrayDataset(data=[[1, 2, 3, 4], [5, 6, 7, 8], [
                       1, 2, 3, 4], [5, 6, 7, 8]], description='b',
                       typecode='f')

    hdul = fits.HDUList()
    hdul.append(fits.PrimaryHDU())
    data = [ima, imb]

    u = fits_dataset(hdul, data)
    assert list(u[1].data[0]) == [1, 2, 3, 4]
    ENDIAN = sys.byteorder  # 'little'
    def ms(i):
        if i in ('big', 'network'):
            return '>'
        if i in ('little', 'native'):
            return '<'
    ENDIAN_MK = ms(ENDIAN)

    assert u[1].data.dtype.str == f'{ENDIAN_MK}i2'
    assert u[2].data.dtype.str == f'{ENDIAN_MK}f4'

def test_arr_toFits():
    ima = ArrayDataset(data=[[1, 2, 3, 4], [5, 6, 7, 8]], description='a')
    u = toFits(ima, file=None)
    # when passed a dataset instead of a list, meta go to PrimaryHDU
    assert issubclass(u.__class__, fits.HDUList)
    assert len(u) == 2
    assert list(u[1].data[0]) == [1, 2, 3, 4]
    assert u[0].header[getFitsKw('description')] == 'a'


def test_tab_fits():
    d = {'col1': aCol(data=[1, 4.4, 5.4E3], unit='eV'),
         'col2': aCol(data=[0, 43, 2E3], unit='cnt')}
    d['col1'].type = 'd'
    d['col2'].type = 'i'
    ds = TableDataset(data=d)
    data = [ds]
    # __import__('pdb').set_trace()
    u = toFits(data, file=None)
    assert issubclass(u.__class__, fits.HDUList)
    print('test_tab_fits', u[0])
    assert u[1].columns['col1'].unit == 'eV'
    assert u[1].data[0][0] == str(d['col1'].data[0])
    assert u[1].data[1][1] == str(d['col2'].data[1])


@pytest.fixture(scope='module')
def make_composite_prd():
    a1 = [768, 4.4, 5.4E3]
    a2 = 'ev'
    a3 = 'arraydset 1'
    a4 = ArrayDataset(data=a1, unit=a2, description=a3)
    a5, a6, a7 = [[1.09, 289], [3455, 564]], 'count', 'arraydset 2'
    # a8 = ArrayDataset(data=a5, unit=a6, description=a7)
    d = {'col1': aCol(data=[1, 4.4, 5.4E3], unit='eV'),
         'col2': aCol(data=[0, -43, 2E3], unit='ct')}
    d['col1'].typecode = 'd'
    d['col2'].typecode = 'i'
    a8 = TableDataset(data=d)
    v = CompositeDataset()
    a9 = 'dataset 1'
    a10 = 'dataset 2'
    v.set(a9, a4)
    v.set(a10, a8)
    assert v[a9] == a4
    a11 = 'm1'
    a12 = NumericParameter(description='a different param in metadata',
                           value=2.3, unit='sec')
    v.meta[a11] = a12
    return v


def test_com_fits(make_composite_prd):
    v = make_composite_prd
    data = [v]
    # __import__('pdb').set_trace()
    u = toFits(data, file=None)
    print(u, len(u))
    assert u[2].data[0] == v['dataset 1'].data[0]
    assert u[2].shape == tuple(v['dataset 1'].shape)
    assert u[3].data['col1'][1] == v['dataset 2']['col1'][1]
    assert u[3].data.dtype[0] == '<f8'


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


def test_toFits_metadata(make_composite_prd):
    for ds in [ArrayDataset, TableDataset, CompositeDataset]:
        if issubclass(ds, ArrayDataset):
            ima = ds(data=[[1, 2, 3, 4], [5, 6, 7, 8]], description='a')
        elif issubclass(ds, TableDataset):
            d = {'col1': aCol(data=[1, 4.4, 5.4E3], unit='eV'),
                 'col2': aCol(data=[0, -43, 2E3], unit='cnt')}
            d['col1'].typecode = 'd'
            d['col2'].typecode = 'i'
            ima = ds(data=d)
        elif issubclass(ds, CompositeDataset):
            # __import__('pdb').set_trace()
            ima = make_composite_prd
        else:
            assert False
        ima.meta['datetime'] = DateParameter(
            '2023-01-23T12:34:56.789012', description='date keyword')
        ima.meta['quat'] = NumericParameter(
            [0.0, 1.1, 2.4, 3.5], description='q')
        ima.meta['float'] = NumericParameter(
            1.234, description='float keyword')
        ima.meta['integer'] = NumericParameter(
            1234, description='integer keyword')
        ima.meta['string_test'] = StringParameter(
            'abc', description=' string keyword')
        ima.meta['boolean_test'] = BooleanParameter(
            True, description=' boolean keyword')
        imb = ArrayDataset(data=[[1, 2, 3, 4], [5, 6, 7, 8], [
                           1, 2, 3, 4], [5, 6, 7, 8]], description='b')

        data = [ima]
        u = toFits(data, file=None)
        assert issubclass(u.__class__, fits.HDUList)
        # assert len(u) == len(data)+1
        # print("-----", u[0].header)
        w = u[1]
        # print(w.header)
        assert w.header['DATETIME'] == '2023-01-23T12:34:56.789012'
        assert w.header['QUAT0'] == 0.0
        assert w.header['QUAT1'] == 1.1
        assert w.header['QUAT2'] == 2.4
        assert w.header['QUAT3'] == 3.5
        assert w.header['FLOAT'] == 1.234
        assert w.header['INTEGER'] == 1234
        assert w.header['STRING_T'] == 'abc'
        assert w.header['BOOLEAN_'] == True

        if issubclass(ds, ArrayDataset):
            assert w.header['NAXIS1'] == len(ima.data[0])
            assert w.header['NAXIS2'] == len(ima.data)
            assert w.header['NAXIS'] == len(ima.shape)
            assert w.data[0][0] == ima[0][0]
            assert w.data[1][1] == ima[1][1]
        elif issubclass(ds, TableDataset):

            assert w.data[0][0] == d['col1'].data[0]
            assert w.data[1][1] == d['col2'].data[1]
        elif issubclass(ds, CompositeDataset):
            pass


def test_prd_fits(make_composite_prd):
    c = make_composite_prd
    p = BaseProduct('abc')
    p['com'] = c
    p.meta['creationDate'] = DateParameter(
        '2023-01-23T12:34:56.789012', description='date keyword')
    v = toFits(p, file=None)

    assert v[2].data[0] == c['dataset 1'].data[0]
    assert v[0].header['DESC'] == 'abc'
    assert v[0].header['TYPE'] == 'BaseProduct'
    assert v[0].header['DATE'] == '2023-01-23T12:34:56.789012'
    v = toFits(p, '/tmp/test.fits', overwrite=1)
    f = fits.open('/tmp/test.fits')
    f.close()
    assert f[0].header == v[0].header
    
    # test stream
    # __import__('pdb').set_trace()
    f = open('/tmp/test.fits', 'wb+')
    stream = toFits(p)
    f.write(stream)
    f.close()
    f = fits.open('/tmp/test.fits')
    f.close()
    assert f[0].header == v[0].header
    del f
    #
    # test is_Fits()
    with open('/tmp/test.fits', 'rb') as f:
        v = f.read()
    assert is_Fits(v)
    assert is_Fits(v, get_type=True) == 'BaseProduct'
    v1 = v.replace(b'TYPE', b'TTTT')
    with pytest.raises(KeyError):
        assert is_Fits(v1, get_type=True) == 'BaseProduct'
    v2= b'U'+v[1:]
    assert not is_Fits(v2)

def test_mapcontext_fits():

    image = Product(description="hi")
    spectrum = Product(description="there")
    simple = Product(description="everyone")

    context = MapContext()
    context.refs.put("x", ProductRef(image))
    context.refs.put("y", ProductRef(spectrum))
    context.refs.put("z", ProductRef(simple))


def test_Fits_Kw():
    # Fits to Parameter name
    assert FITS_KEYWORDS['DATASUM'] == 'checksumData'
    assert FITS_KEYWORDS['DESC'] == 'description'
    assert FITS_KEYWORDS['CUNIT'] == 'cunit'
    assert getFitsKw('checksumData') == 'DATASUM'
    assert getFitsKw('description') == 'DESC'
    assert getFitsKw('cunit01') == 'CUNIT01'
    assert getFitsKw('description01234') == 'DES01234'
    assert getFitsKw('description01234', ndigits=2) == 'DESC34'
    # with pytest.raises(ValueError):
    assert getFitsKw('checksumData0123', 3) == 'DATAS123'
    assert getFitsKw('checksumData0123', 2) == 'DATASU23'
    with pytest.raises(ValueError):
        # wrong format in `extra`
        assert getFitsKw('foo0123', 5, (('foo', 'BAR'))) == 'BAR00123'
    assert getFitsKw('foo0123', 5, (('foo', 'BAR'),)) == 'BAR00123'
    # multi
    lst = getFitsKw('startDate', multi=True)
    assert all(r in lst for r in ('DATE-OBS', 'DATE_OBS', 'DATE-BEG', 'DATE_BEG'))
    assert getFitsKw('creationDate', multi=True) == ['DATE']
    
def test_fits_header_list():
    fn = 'tests/'+'resources/SD_24_0791_20170101T000324_0078972002.fits'
    assert fits_header_list(fn)[0].header['DESC'] == 'SVOM VT Single Exposure (VTSE) 1B v1.32.2-0-g0a61c71'
    with open(fn, 'rb') as f:
        blob = f.read()
    assert is_Fits(blob)
    assert fits_header_list(blob)[0].header['DESC'] == 'SVOM VT Single Exposure (VTSE) 1B v1.32.2-0-g0a61c71'

def test_write_to_file():
    fn = 'tests/'+'resources/SD_24_0791_20170101T000324_0078972002.fits'
    assert fits_header_list(fn)[0].header['DESC'] == 'SVOM VT Single Exposure (VTSE) 1B v1.32.2-0-g0a61c71'
    with open(fn, 'rb') as f:
        blob = f.read()
    assert is_Fits(blob)
    tf = f'/tmp/It_is_True'
    try:
        os.unlink(tf)
    except OSError:
        pass
    filepath = write_to_file(blob, '/tmp/It_is_${SIMPLE}')
    assert filepath == tf
    with open(tf, 'rb') as f:
        blob2 = f.read()
    assert blob == blob2
