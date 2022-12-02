# -*- coding: utf-8 -*-

from .fits_kw import FITS_KEYWORDS, getFitsKw
from ..dataset.arraydataset import ArrayDataset
from ..dataset.tabledataset import TableDataset
from ..dataset.dataset import CompositeDataset
from ..dataset.unstructureddataset import UnstructuredDataset
from ..dataset.dataset import Dataset
from ..dataset.datatypes import DataTypes
from ..dataset.baseproduct import BaseProduct
from ..dataset.dateparameter import DateParameter
from ..dataset.stringparameter import StringParameter
from ..dataset.numericparameter import NumericParameter, BooleanParameter
from ..dataset.datatypes import Vector

import os
from collections.abc import Sequence
import io

FITS_INSTALLED = True
try:
    import numpy as np
    from astropy.io import fits
    from astropy.table import Table
    from astropy.table import Column
except ImportError:
    FITS_INSTALLED = False

debug = False
typecode2np = {
    "b": np.int8,    # signed char
    "B": np.uint8,   # unsigned char
    "u": str,     # string
    "h": np.int16,   # signed short
    "H": np.uint16,  # unsigned integer
    "i": np.int16,   # signed integer
    "I": np.uint16,  # unsigned integer
    "l": np.int32,   # signed long
    "L": np.uint32,  # unsigned long
    "q": np.int64,   # signed long long
    "Q": np.uint64,  # unsigned long long
    "f": np.float32,  # float
    "d": np.float64,   # double
    "c": np.complex64,  # complex
    "c128": np.complex128,  # complex 128 b
    "t": bool,       # truth value
    "V": np.void,       # raw bytes block of fixed length
    "U": str
}


def main():
    fitsdir = '/Users/jia/desktop/vtse_out/'
    if os.path.exists(fitsdir + 'array.fits'):
        os.remove(fitsdir + 'array.fits')
    ima = ArrayDataset(data=[[1, 2, 3, 4], [5, 6, 7, 8]], description='a')
    imb = ArrayDataset(data=[[1, 2, 3, 4], [5, 6, 7, 8], [
                       1, 2, 3, 4], [5, 6, 7, 8]], description='b')
    # im=[[1,2,3,4],[5,6,7,8]]
    hdul = fits.HDUList()
    fits_dataset(hdul, [ima, imb])


def toFits(data, file='', **kwds):
    """convert dataset to FITS.

    :data: a list of Dataset or a BaseProduct (or its subclass).
    :file: '' for returning fits stream. string for file name. default ''.
    """
    # __import__('pdb').set_trace()
    hdul = fits.HDUList()
    hdul.append(fits.PrimaryHDU())
    if issubclass(data.__class__, (BaseProduct)):
        sets = data.values()
        names = list(data.keys())
        hdul = fits_dataset(hdul, sets, names)
        add_header(data.meta, hdul[0].header)
        hdul[0].header['EXTNAME'] = 'PrimaryHDU'
    elif issubclass(data.__class__, (ArrayDataset, TableDataset, CompositeDataset)):
        if issubclass(data.__class__, (ArrayDataset)):
            # dataset -> fits
            sets = [data]
            names = ['IMAGE']
        elif issubclass(data.__class__, (TableDataset)):
            sets = [data]
            names = ['TABLE']
        elif issubclass(data.__class__, (CompositeDataset)):
            sets = data.values()
            names = list(data.keys())
        hdul = fits_dataset(hdul, sets, names)
        # when passed a dataset instead of a list, meta go to PrimaryHDU
        add_header(data.meta, hdul[0].header)
    elif issubclass(data.__class__, Sequence) and \
            issubclass(data[0].__class__, (ArrayDataset, TableDataset, CompositeDataset)):
        hdul = fits_dataset(hdul, data)
    else:
        raise TypeError(
            'Making FITS needs a dataset or a product, or a Sequence of them.')
    if file:
        hdul.writeto(file, **kwds)
        return hdul
    elif file == '':
        with io.BytesIO() as iob:
            hdul.writeto(iob, **kwds)
            fits_im = iob.getvalue()
        return fits_im
    else:
        return hdul


def fits_dataset(hdul, dataset_list, name_list=None, level=0):
    """ Fill an HDU list with dataset data.

    :hdul: `list` of HDUs. 
    :dataset_list: `list` of dataset subclasses.
    :name_list:
    """
    if name_list is None:
        name_list = []

    dataset_only = issubclass(
        dataset_list.__class__, (ArrayDataset, TableDataset, CompositeDataset))

    for n, ima in enumerate(dataset_list):
        header = fits.Header()
        if issubclass(ima.__class__, ArrayDataset):
            a = np.array(ima)
            if not dataset_only:
                header = add_header(ima.meta, header)
            ename = ima.__class__.__name__ if len(
                name_list) == 0 else name_list[n]
            header['EXTNAME'] = ename
            hdul.append(fits.ImageHDU(a, header=header))
        elif issubclass(ima.__class__, TableDataset):
            t = Table()
            for name, col in ima.items():
                tname = typecode2np['u' if col.typecode == 'UNKNOWN' else
                                    'u' if col.typecode.endswith('B') else
                                    col.typecode]
                if debug:
                    print('tname:', tname)
                c = Column(data=col.data, name=name, dtype=tname, shape=[
                ], length=0, description=col.description, unit=col.unit, format=None, meta=None, copy=False, copy_indices=True)
                t.add_column(c)
            if not dataset_only:
                header = add_header(ima.meta, header)
            ename = ima.__class__.__name__ if len(
                name_list) == 0 else name_list[n]
            header['EXTNAME'] = ename
            hdul.append(fits.BinTableHDU(t, header=header))
        elif issubclass(ima.__class__, CompositeDataset):
            if not dataset_only:
                header = add_header(ima.meta, header)
            hdul.append(fits.BinTableHDU(Table(), header=header))
            for name, dlist in ima.items():
                #print('dlist', dlist.__class__)
                fits_dataset(hdul, [dlist], name_list=[name], level=level+1)
        elif issubclass(ima.__class__, UnstructuredDataset):
            raise NotImplemented("UnstructuredDataset not yet supported")
        else:
            raise TypeError('Must be a Dataset to convert to fits.')
    if debug:
        print("****", len(hdul))
    return hdul

    #hdul.writeto(fitsdir + 'array.fits')

   # f = fits.open(fitsdir + 'array.fits')
   # print(len(f))
    #h1 = f[0].header
    #h2 = f[1].header
    # print(h2)
    # return h1


def add_header(meta, header):
    """ Populate  header with keyword lines extracted from MetaData.

    :meta: :class: `MetaData`
    """
    for name, param in meta.items():
        pval = param.value
        if pval is None:
            v = fits.card.Undefined()
            kw = getFitsKw(name)
            header[kw] = (v, param.description)
        elif issubclass(param.__class__, DateParameter):
            value = pval.isoutc() if pval.tai else fits.card.Undefined()
            kw = getFitsKw(name)
            header[kw] = (value, param.description)
        elif issubclass(param.__class__, NumericParameter):
            if issubclass(pval.__class__, (Sequence)):
                for i, com in enumerate(pval):
                    kw = getFitsKw(name, ndigits=1)+str(i)
                    header[kw] = (com, param.description+str(i))
                    if debug:
                        print(kw, com)
            else:
                kw = getFitsKw(name)
                header[kw] = (pval, param.description)
        elif issubclass(param.__class__, StringParameter):
            kw = getFitsKw(name)
            if pval == 'UNKNOWN':
                v = fits.card.Undefined()
            else:
                v = pval
            header[kw] = (v, param.description)
        elif issubclass(param.__class__, BooleanParameter):
            kw = getFitsKw(name)
            v = 'T' if pval else 'F'
            header[kw] = (v, param.description)
        else:
            kw = getFitsKw(name)
            v = fits.card.Undefined()
            header[kw] = (v, '%s of unknown type' % str(pval))
    if debug:
        print('*** add_header ', header)
    return header


def fits_header():
    fitsdir = '/Users/jia/desktop/vtse_out/'
    f = fits.open(fitsdir + 'array.fits')
    h = f[0].header
    #h.set('add','header','add a header')
    h['add'] = ('header', 'add a header')
    h['test'] = ('123', 'des')
    f.close()

    return h


def test_fits_kw(h):
    # print(h)
    # print(list(h.keys()))
    #assert FITS_KEYWORDS['CUNIT'] == 'cunit'
    assert getFitsKw(list(h.keys())[0]) == 'SIMPLE'
    assert getFitsKw(list(h.keys())[3]) == 'NAXIS1'


if __name__ == '__main__':

    # test_fits_kw(fits_data())
    main()
