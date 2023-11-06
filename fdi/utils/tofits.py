# -*- coding: utf-8 -*-

from .fits_kw import FITS_KEYWORDS, getFitsKw
from ..dataset.arraydataset import ArrayDataset
from ..dataset.tabledataset import TableDataset
from ..dataset.dataset import CompositeDataset
from ..dataset.serializable import Serializable
from ..dataset.unstructureddataset import UnstructuredDataset
from ..dataset.dataset import Dataset
from ..dataset.datatypes import DataTypes
from ..dataset.baseproduct import BaseProduct
from ..dataset.dateparameter import DateParameter
from ..dataset.stringparameter import StringParameter
from ..dataset.numericparameter import NumericParameter, BooleanParameter
from ..dataset.datatypes import Vector
from ..pal.context import RefContainer
from .common import lls

import os
from collections.abc import Sequence
import io
from string import Template
import logging
# create logger
logger = logging.getLogger(__name__)
logger.debug('logging level %d' % (logger.getEffectiveLevel()))


FITS_INSTALLED = True
try:
    import numpy as np
    from astropy.io import fits
    from astropy.io.fits import HDUList
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

def is_Fits(data, get_type=False):
    """ Determine if data is a FITS blob and return CARD/TYPE name if needed.

    Parameter
    ---------
    data : object. string is encoded to `bytes` with utf-8.
    get_type : bool
        If set return the TYPE or CARD name. Default is `False`. If set search all positions at 80 bytes interval for 'TYPE' and 'CARD' keyword and name up to '/'.

    Returns
    -------
    bool, string

    Exception
    ---------
        If `get_card` is set and TYPE/CARD or name is not found, raise KeyError.
    """
    ID = b'SIMPLE  =                    T'
    strp = b"""" '"""

    if issubclass(data.__class__, str):
        data = data.encode('utf-8')
        
    try:
        y= data.startswith(ID)
    except:
        return False
    if y:
        if get_type:
            cls = None
            for i in range(0, min(1800, len(data)), 80):
                if data[i:i+8].strip() in (b'TYPE', b'CARD'):
                    cls = data[i+10:i+80].split(b'/',1)[0].strip(strp)
                    break
            if not cls:
                raise KeyError('TYPE or CARD name not found.')
            else:
                # found TYPE/CARD and a name with positive length.
                return cls.decode('ascii')
        else:
            # no need for TYPE/CARD
            return True
    else:
        # ID not found.
        return False
    
def convert_name(n):
    """ Converts model/card/definition/product name to comply to Python class naming convention.
    """
    name = n.replace('-', '_')
    return name


def toFits(data, file='', **kwds):
    """convert dataset to FITS.

    :data: a list of Dataset or a BaseProduct (or its subclass).
    :file: A non-empty string for file name. `None` means return HDUList only. Default '', for only returning fits stream/BLOB. 
    """

    hdul = fits.HDUList()
    hdul.append(fits.PrimaryHDU())
    if issubclass(data.__class__, (BaseProduct)):
        sets = list(data.values())
        names = list(data.keys())
        sets.append(data.history)
        names.append('history')
        hdul = fits_dataset(hdul, sets, names)
        add_header(data.meta, hdul[0].header, data.zInfo['metadata'])
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
    elif file is None:
        return hdul
    else:
        with io.BytesIO() as iob:
            hdul.writeto(iob, **kwds)
            fits_im = iob.getvalue()
        return fits_im


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
        elif issubclass(ima.__class__, (TableDataset, RefContainer)):
            if issubclass(ima.__class__, RefContainer):
                ima = ima.toTable()
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
            if not dataset_only and not isinstance(ima, RefContainer):
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
                # print('dlist', dlist.__class__)
                fits_dataset(hdul, [dlist], name_list=[name], level=level+1)
        elif issubclass(ima.__class__, UnstructuredDataset):
            raise NotImplemented("UnstructuredDataset not yet supported")
        else:
            raise TypeError('Must be a Dataset to convert to fits.')
    if debug:
        print("****", len(hdul))
    return hdul

    # hdul.writeto(fitsdir + 'array.fits')

   # f = fits.open(fitsdir + 'array.fits')
   # print(len(f))
    # h1 = f[0].header
    # h2 = f[1].header
    # print(h2)
    # return h1


def add_header(meta, header, zim={}):
    """ Populate  header with keyword lines extracted from MetaData.

    :meta: :class: `MetaData`
    :zim: `zInfo['metadata']` for lookingup FITS keywords.

    """
    for name, param in meta.items():
        pval = param.value
        if name in zim and 'fits_keyword' in zim[name]:
            kw = zim[name]['fits_keyword']
            ex = ((name, kw),)
        else:
            ex = None
        if pval is None:
            v = fits.card.Undefined()
            kw = getFitsKw(name, extra=ex)
            header[kw] = (v, param.description)
        elif issubclass(param.__class__, DateParameter):
            value = pval.isoutc() if pval.tai else fits.card.Undefined()
            kw = getFitsKw(name, extra=ex)
            header[kw] = (value, param.description)
        elif issubclass(param.__class__, NumericParameter):
            if issubclass(pval.__class__, (Sequence, list)):
                for i, com in enumerate(pval):
                    kw = getFitsKw(name, ndigits=1, extra=ex)[:7]+str(i)
                    header[kw] = (com, param.description+str(i))
                    if debug:
                        print(kw, com)
            elif issubclass(pval.__class__, (Vector)):
                for i, com in enumerate(pval.components):
                    kw = getFitsKw(name, ndigits=1, extra=ex)[:7]+str(i)
                    header[kw] = (com, param.description+str(i))
            else:
                kw = getFitsKw(name, extra=ex)
                header[kw] = (pval, param.description)
        elif issubclass(param.__class__, StringParameter):
            kw = getFitsKw(name, extra=ex)
            if pval == 'UNKNOWN':
                v = fits.card.Undefined()
            else:
                v = pval
            header[kw] = (v, param.description)
        elif issubclass(param.__class__, BooleanParameter):
            kw = getFitsKw(name, extra=ex)
            v = 'T' if pval else 'F'
            header[kw] = (v, param.description)
        else:
            kw = getFitsKw(name, extra=ex)
            v = fits.card.Undefined()
            header[kw] = (v, '%s of unknown type' % str(pval))
    if debug:
        print('*** add_header ', header)
    return header


def fits_header_list(fitsobj):
    """ Returs HDUList given fits file name or a readable object. """
    if issubclass(fitsobj.__class__, str):
        fitspath = fitsobj
        with fits.open(fitspath, memmap=True, lazy_load_hdus=False) as hdul:
            h = hdul
            return h
    elif issubclass(fitsobj.__class__, bytes):
        #with io.BytesIO(fits) as iob:
        h = []
        hdul = HDUList(h, file=fitsobj)
        return hdul
    else:
        raise ValueError('Need bytes or file name')
    # h.set('add','header','add a header')
    #h['add'] = ('header', 'add a header')
    #h['test'] = ('123', 'des')


def write_to_file(p, fn, dct=None, ignore_type_error=False):    
    """write out fits file for the given product and try to send samp notices.

    Parameters
    ----------
    p : Serializable, bytes, or HDUList
        The product that can be a BLOB, fits HDU list,
        `BaseProduct` (or `Serializable`). Or else quietly pass.
    fn : str
        fits file path. it will go throug template expansion using FITS keywords name to their values. E.g. "It is $SIMPLE." becomes "It is True."
    dct : Mapping
        A dictionary for translating keys in `fn` to values. Default is `None` which uses the `PrimaryHDU.header`.
    ignore_type_error: if set, do not raise `TypeError` if `p` is not acceptable.
    Returns
    -------
    str
        expanded fits file path. or the input `fn` if the product has wrong format and `ignore_type_error` is set.

    Examples
    --------
    FIXME: Add docs.

    """

    if not fn:
        raise ValueError('Bad product file name: %s.' % str(fn))

    if not (issubclass(p.__class__, Serializable) or \
       issubclass(p.__class__, HDUList) or \
       is_Fits(p)):

        raise TypeError(f"{lls(p, 100)} is not FITS data.")
    
    if issubclass(p.__class__, Serializable):
        p = p.fits()

    sp = fn
    if '${' in fn:
        # get a k-v dictionary  for this data
        kv = dct if dct else dict(
            (k, (v.strip() if issubclass(v.__class__, str) else v)) \
             for k,v in fits_header_list(p)[0].header.items())

        # expand name
        #kv = {'date-obs':'ASD', 'e-o':'4543'}
        #sp = '${date-obs} ${e-o}'

        for k,v in kv.items():
            if '${' in sp:
                if isinstance(v, bool):
                    _v = 'T' if v else 'F'
                else:
                    _v = str(v)
                sp = sp.replace(('${%s}' % k), _v)
            else:
                break

    try:
        with open(sp, 'wb') as fitsf:
            if is_Fits(p):
                fitsf.write(p)
            elif issubclass(p.__class__, HDUList):
                p.writeto(fitsf)
            else:
                pass
            print('**', sp)
    except TypeError as e:
        if ignore_type_error:
            return fn
        logger.debug('error writing FITS:'+str(e))
        raise
    logger.debug(f"{sp} ({fn if sp != fn else ''})")

    return sp

def send_samp(filepath, client, **kwds):
    """Send url and name notify messages by SAMP.

    Parameters
    ----------
    filepath : str
        for making URL and name.
    client : SAMPclient
        SAMP client
    kwds : dict
        extra kv to add to parameters.

    Returns
    -------
    int
        -1 for not connected, rest from `client.notify_all`.

    Examples
    --------
    FIXME: Add docs.

    """
    
    if client.is_connected:
        params = dict(
            url=f'file://{filepath}',
            name=filepath.rsplit('/',1)[-1]
        )
        params.update(kwds)
        
        message = {}
        message["samp.mtype"] = "image.load.fits"
        message["samp.params"] = params
        return client.notify_all(message)
    else:
        logger.debug('SAMP hub not conncted.')
        return -1
    
if __name__ == '__main__':

    # test_fits_kw(fits_data())
    main()
