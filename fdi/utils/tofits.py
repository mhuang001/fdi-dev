# -*- coding: utf-8 -*-

from .fits_kw import Key_Words, getFitsKw, FitsParameterName_Look_Up
from ..dataset.arraydataset import ArrayDataset
from ..dataset.tabledataset import TableDataset
from ..dataset.dataset import CompositeDataset
from ..dataset.serializable import Serializable, serialize
from ..dataset.unstructureddataset import UnstructuredDataset
from ..dataset.dataset import Dataset
from ..dataset.datatypes import DataTypes, typecode2np
from ..dataset.baseproduct import BaseProduct
from ..dataset.dateparameter import DateParameter
from ..dataset.stringparameter import StringParameter
from ..dataset.numericparameter import NumericParameter, BooleanParameter
from ..dataset.attributable import value2parameter
from ..dataset.datatypes import Vector
from ..pal.context import RefContainer
from .common import lls

import os
from collections.abc import Sequence
import io
import copy
import datetime
import itertools
import logging
# create logger
logger = logging.getLogger(__name__)
logger.debug('logging level %d' % (logger.getEffectiveLevel()))
import re

Template_Pattern = re.compile(r"\${([\w-]+)+}")
""" Use this rule to parse templates. """

FITS_INSTALLED = True

try:
    import numpy as np
    from astropy.io import fits
    from astropy.io.fits import HDUList
    from astropy.table import Table
    from astropy.table import Column
except ImportError:
    FITS_INSTALLED = False

FITSKW_VECTOR_XYZ_INDEX = {0:'X', 1:'Y', 2:'Z'}
""" What to use for labeling the components, x,y,z or 0,1,2. """

debug = False


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


def toFits(data, file='', headers_only=False, **kwds):
    """convert dataset to FITS.

    Sets "Astronomers ID" for the data product to data and the fits.
    
    :data: a list of Dataset or a BaseProduct (or its subclass).
    :file: A non-empty string for file name. `None` means return HDUList only. Default '', for only returning fits stream/BLOB.
    :headers_only: Only fill the headers (metadata).
    """

    hdul = fits.HDUList()
    hdul.append(fits.PrimaryHDU())

    if issubclass(data.__class__, (BaseProduct)):
        sets = list(data.values())
        names = list(data.keys())
        sets.append(data.history)
        names.append('history')
        if not headers_only:
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
            issubclass(data[0].__class__, (ArrayDataset, TableDataset, CompositeDataset, UnstructuredDataset)):
        hdul = fits_dataset(hdul, data) #, data.zInfo['metadata'])
    else:
        raise TypeError(
            'Making FITS needs a dataset or a product, or a Sequence of them.')

    sp = expand_template(hdul, fn=get_template(data))
    value = sp.replace(':', '').replace(' ', '_')

    desc = 'Astronomers product ID'
    if issubclass(data.__class__, (BaseProduct)):
        zim = data.zInfo['metadata']
        if 'aId' in zim:
            x = value2parameter('aId', value, zim)
            if data.meta['aId'] != x:
                data.meta['aId'] = x
                hdul[0].header['aId'] = (value, desc)
        else:
            data.meta['aId'] = StringParameter(value, desc)
            hdul[0].header['aId'] = (value, desc)
    
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
    :dataset_list: `Sequence` of dataset subclasses.
    :name_list:
    """
    if name_list is None:
        name_list = []

    dataset_only = issubclass(
        dataset_list.__class__, (ArrayDataset, TableDataset, CompositeDataset))

    for n, ima in enumerate(dataset_list):
        header = fits.Header()
        if issubclass(ima.__class__, ArrayDataset):
            try:
                dt = ima.meta.get('numpyType', None)
                if dt is None or not dt.value:
                    dt = typecode2np.get(ima.meta['typecode'].value, None)
                    
                else:
                    dt = dt.value

                a = np.array(ima, dtype=dt)
            except ValueError as e:
                ima.data = list(itertools.chain(*ima.data))
                ima.meta['numpy'] = StringParameter(str(e),
                                                    description='Numpy conversion error')
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
            raise NotImplementedError("UnstructuredDataset not yet supported")
        else:
            raise TypeError('Must be a Dataset to convert to fits.')
    if debug:
        print("**** tofits.py", len(hdul))
    return hdul

    # hdul.writeto(fitsdir + 'array.fits')

   # f = fits.open(fitsdir + 'array.fits')
   # print(len(f))
    # h1 = f[0].header
    # h2 = f[1].header
    # print(h2)
    # return h1

def fits_standard_text(c):
    if issubclass(c.__class__, bytes):
        r = c.decode(encoding="ascii", errors="backslashreplace")
    elif issubclass(c.__class__, str):
        r = ascii(c)[1:-1]
        # c.encode(encoding="ascii", errors="backslashreplace")
        #r = c.replace('\n','\\n')
    else:
        r = c
    return r

def set_parameter_to_header(param, header, name, ex, ignore_error=False, debug=debug):
    """Set the value of a `Parameter` to the FITS header.

    Parameters
    ----------
    param : Parameter
        A `Parameter` or its subclass. If a string is given, set to the header.
    header : `HDU` header
        The header of an HDU of a FITS.
    name : str
        name of the parameter.
    ex : dict
        A list of key-vals to be sent to `getFitsKw`.
    ignore_error : bool
        If set, exceptions will not be raised. Skip this parameter.
    debug : bool
        prints more debugging info.

    Returns
    -------
    HDU header
        give back the (usually) modified header.

    Raises
    ------
    ValueError

    Examples
    --------
         If None is given, `ValueError` is thrown. 


    """
    
    if param is None:
        if ignore_error:
            return header
        raise ValueError(f'Cannot get value from None param {param}.')

    pval = getattr(param, 'value', None)

    if pval is None:
        v = fits.card.Undefined()
        kw = getFitsKw(name, extra=ex)
        c = 'null value'
        c = fits_standard_text(c)
        header[kw] = (v, c)
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
                kw = getFitsKw(name, ndigits=1, extra=ex)
                if len(pval.components) < 4:
                    ind = FITSKW_VECTOR_XYZ_INDEX[i]
                else:
                    ind = str(i)
                kw = kw[:7] + ind
                header[kw] = (com, param.description+ind)
        else:
            kw = getFitsKw(name, extra=ex)
            header[kw] = (pval, param.description)
    elif issubclass(param.__class__, StringParameter):
        kw = getFitsKw(name, extra=ex)
        if pval == 'UNKNOWN':
            v = fits.card.Undefined()
        else:
            v = pval
        c = param.description
        _c = fits_standard_text(c)
        # c.encode(encoding="ascii",errors="backslashreplace")
        _v = fits_standard_text(v)
        header[kw] = (_v, _c)
    elif issubclass(param.__class__, BooleanParameter):
        kw = getFitsKw(name, extra=ex)
        v = bool(pval)
        header[kw] = (v, param.description)
    else:
        kw = getFitsKw(name, extra=ex)
        v = fits.card.Undefined()
        des = getattr(param, 'description', 'Parameter "%s" of unknown type' % str(pval))
        header[kw] = (v, des)
    return header
    
def add_header(meta, header, zim={}):
    """ Populate  header with keyword lines extracted from MetaData.

    :meta: :class: `MetaData`
    :zim: `zInfo['metadata']` for lookingup FITS keywords and set the order of keywords. Default is None.

    """
    # if zim:
    #     mc = copy.copy(meta)
    #     lst = []
    #     for i, name in enumerate(meta.keys()):
    #         if name in zim:
    #             lst.append(name)
    #             mc.pop(name)
    #     lst.extend(mc.keys())
    # else:
    #     lst = list(meta)

    lst = list()
    lst.extend(set(zim) | set(meta))
    for name in lst:
        kw = -1
        if name in meta:
            # first check if fits can be found in meta, including non-SDPs.
            param = meta[name]
            kw = getattr(param, 'fits_keyword', None)
            ex = ((name, kw),) if kw else None
        if (kw == -1) and not (name in zim):
            raise KeyError(f"{name} was not found in meta or zim when generating FITS.")
        if (kw is None or kw == -1) and name in zim:
            kw = zim[name].get('fits_keyword', None)
            ex = ((name, kw),) if kw else None
        header = set_parameter_to_header(param, header, name, ex, ignore_error=False, debug=debug)

    if debug:
        print('*** add_header ', header)
    return header


def fits_header_list(fitsobj):
    """ Returns HDUList given fits file name or a readable object. """

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

def get_template(f):
    template = ''
    if issubclass(f.__class__, HDUList):
        template = f[0].header['AIDTEMPL']
    elif is_Fits(f):
        _t = f[:2300].split(b'AIDTEMPL= ',1)
        if len(_t) > 1:
            template = _t[1][:80-len('AIDTEMPL= ')].split(b'/', 1)[0].strip().strip(b"'")
            template = template.decode('ascii')
    elif issubclass(f.__class__, BaseProduct):
        template = f.meta.get('aIdTemplate', '')
        if template:
            template = template.value
    return template

def expand_template(p, fn, dct=None):    
    """
    Parameters
    ----------
    p : Serializable, bytes, or HDUList
        The product that can be a BLOB, fits HDU list,
        `BaseProduct` (or `Serializable`). Or else quietly pass.
    fn : str
        String with templates. it will go throug template expansion using FITS keywords name to their values. E.g. "It is $SIMPLE." becomes "It is True."
    dct : Mapping
        A dictionary for translating keys in `fn` to values. Default is `None` which uses the `PrimaryHDU.header`.
    Returns
    -------
    str
        expanded string expanded by fits blob key-value set and `dct`. Logical values are 'True' and 'False'.

    Examples
    --------
    FIXME: Add docs.

    """

    if '${' in fn:
        lst = p if issubclass(p.__class__, HDUList) else  fits_header_list(p)
        # get a k-v dictionary  for this data
        kv = dct if dct else lst[0].header
    
        # expand name
        #kv = {'date-obs':'ASD', 'e-o':'4543'}
        #sp = '${date-obs} ${e-o}'
        def try_time(k):
            sv = str(k)
            try:
                d = datetime.datetime.fromisoformat(sv)
                #sv = "%s.%06d" % (d.strftime('%y%m%dX%H%M%S'), d.microseconds))
                #x = 'B' if 'B' in sv else 'T'
                sv = sv.replace(':','').replace('-','')
            except ValueError:
                pass
            return sv
        pars = re.findall(Template_Pattern, fn)
        sp = fn
        # expand kwfound in p and try - _ if needed
        for k in pars:
            if k in kv:
                sv = try_time(kv[k])
                sp = sp.replace('${%s}' % k, sv)
            else:
                try:
                    nm = FitsParameterName_Look_Up[k]
                except LookupError:
                    nm = k
                for kk in getFitsKw(nm, multi=True):
                    if kk != k and kk in kv:
                        sv = try_time(kv[kk])
                        sp = sp.replace('${%s}' % k, sv)
                        break
        logger.debug(f'Template {fn} is expanded to {sp}.')
    else:
        logger.debug(f'Template {fn} is expanded.')
        sp = fn
    
    return sp.replace('${', '').replace('}', '')
        
def write_to_file(p, fn, dct=None, ignore_type_error=False, this_fits=None, indent=None, cmd=None, expand_only=False):
    """write out fits file for the given product and try to send samp notices.
    If product is `BaseProduct` (or `Serializable`),

    Parameters
    ----------
    p : Serializable, bytes, or HDUList
        The product that can be a BLOB, fits HDU list,
        `BaseProduct` (or `Serializable`). Or else raise `TypeError`.
    fn : str
        fits file path. it will go throug template expansion using FITS keywords name to their values. E.g. "It is $SIMPLE." becomes "It is True."
    dct : Mapping
        A dictionary for translating keys in `fn` to values. Default is `None` which uses the `PrimaryHDU.header`.
    this_fits : bytes or HDUList
        Use this if FITS representation is needed. Default is `None`.
    indent : int
        If to save in JSON, how much indentation is set. Default None.
    cmd : str or None
        command_line of `--fits`.
    expand_only : Return expanded path without writing to file.
    
    Returns
    -------
    str
        expanded fits file path. or the input `fn` if the product has wrong format and `ignore_type_error` is set. Logical values are 'True' and 'False'.

    Examples
    --------
    FIXME: Add docs.
    """
    if not fn:
        raise ValueError('Bad product file name: %s.' % str(fn))
    if not (issubclass(p.__class__, Serializable) or \
       issubclass(p.__class__, HDUList) or \
       issubclass(p.__class__, dict) or \
       is_Fits(p)):

        raise TypeError(f"{lls(p, 100)} is not writable data.")
    _p = None
    if issubclass(p.__class__, Serializable):
        if cmd and cmd.strip():
            # cmd line
            if is_Fits(this_fits):
                _p = this_fits
            else:
                # make one
                _p = p.fits()
            sp = expand_template(_p, fn, dct)
                
        else:
            # only need headers to fill template
            if is_Fits(this_fits):
                _p = this_fits
            else:
                _p = p.fits(headers_only=True)
            sp = expand_template(_p, fn, dct)
            _p = None
    else:
        sp = expand_template(p, fn, dct)
        
    sp = sp.replace(':', '').replace(' ', '_')

    logger.debug(f"{sp} ({fn})" if sp != fn else f"{sp}")
    if expand_only:
        return sp
    
    try:
        if is_Fits(p):
            with open(sp, 'wb') as prodf:
                prodf.write(p)
        elif issubclass(p.__class__, HDUList):
            with open(sp, 'wb') as prodf:
                p.writeto(prodf)
        else:
            with open(sp, 'w+') as prodf:
                prodf.write(serialize(p, indent=indent))
            # logger.info(f'Cannot save {p.__class__} to FITS.')
            # cmd line
            if _p:
                _sp = os.path.splitext(sp)[0] + '.fit'
                with open(_sp, 'wb') as prodf:
                    prodf.write(_p)

    except TypeError as e:
        if ignore_type_error:
            return sp
        logger.debug('error writing file:'+str(e))
        raise

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
