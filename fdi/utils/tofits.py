from fdi.utils.fits_kw import FITS_KEYWORDS,getFitsKw
from fdi.dataset.arraydataset import ArrayDataset
from fdi.dataset.tabledataset import TableDataset
from fdi.dataset.dataset import CompositeDataset
from fdi.dataset.dataset import Dataset
from fdi.dataset.datatypes import DataTypes
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.dateparameter import DateParameter
from fdi.dataset.stringparameter import StringParameter
from fdi.dataset.numericparameter import NumericParameter, BooleanParameter
from fdi.dataset.datatypes import Vector
from astropy.io import fits
from astropy.table import Table
from astropy.table import Column
import numpy as np
import os

debug = False
typecode2np = {
    "b": np.int8,    # signed char
    "B": np.uint8,   # unsigned char
    "u": np.str,     # string
    "h": np.int16,   # signed short
    "H": np.uint16,  # unsigned integer
    "i": np.int16,   # signed integer
    "I": np.uint16,  # unsigned integer
    "l": np.int32,   # signed long
    "L": np.uint32,  # unsigned long
    "q": np.int64,   # signed long long
    "Q": np.uint64,  # unsigned long long
    "f": np.float32, # float
    "d": np.float64,   # double
    "c": np.complex64, # complex
    "c128": np.complex128, # complex 128 b
    "t": np.bool       # truth value
}

def main():
    fitsdir = '/Users/jia/desktop/vtse_out/'
    if os.path.exists(fitsdir + 'array.fits'):
        os.remove(fitsdir + 'array.fits')
    ima=ArrayDataset(data=[[1,2,3,4],[5,6,7,8]], description='a')
    imb=ArrayDataset(data=[[1,2,3,4],[5,6,7,8],[1,2,3,4],[5,6,7,8]], description='b')
    #im=[[1,2,3,4],[5,6,7,8]]
    hdul = fits.HDUList()
    fits_dataset(hdul,[ima,imb])

def toFits(data, file=None,**kwds):
    """convert dataset to FITS.
    
    :data: a list of Dataset or a BaseProduct.
    """
    #__import__('pdb').set_trace()
    hdul = fits.HDUList()
    hdul.append(fits.PrimaryHDU())
    if not issubclass(data.__class__,list):
        if issubclass(data.__class__, BaseProduct):
            hdul=fits_dataset(hdul,data.values())
            add_header(data.meta,hdul[0].header)
            if file:
                hdul.writeto(file,**kwds)
            return hdul
        else:
            raise ValueError('must be dataset of a product')
    if issubclass(data[0].__class__, (ArrayDataset, TableDataset,CompositeDataset)):
        hdul=fits_dataset(hdul,data)
    if file:
        hdul.writeto(file,**kwds)
    return hdul

def fits_dataset(hdul,dataset_list):
    for n, ima in enumerate(dataset_list):
        header = fits.Header()
        if issubclass(ima.__class__, ArrayDataset):
            a=np.array(ima)
            header=add_header(ima.meta,header)
            hdul.append(fits.ImageHDU(a,header=header))
        elif issubclass(ima.__class__, TableDataset):
            t=Table()
            for name, col in ima.items():
                tname=typecode2np['u' if col.typecode=='UNKNOWN' else col.typecode]
                if debug:
                    print('tname:',tname)
                c=Column(data=col.data, name=name, dtype=tname, shape=(), length=0, description=col.description, unit=col.unit, format=None, meta=None, copy=False, copy_indices=True)
                t.add_column(c)
            header=add_header(ima.meta,header)
            hdul.append(fits.BinTableHDU(t,header=header))
        elif issubclass(ima.__class__, CompositeDataset):
            for name, dlist in ima.items():
                print('dlist',dlist.__class__)
                fits_dataset(hdul,[dlist])
    if debug:
        print("****",len(hdul))
    return hdul

    #hdul.writeto(fitsdir + 'array.fits')
    
   # f=fits.open(fitsdir + 'array.fits')
   # print(len(f))
    #h1=f[0].header
    #h2=f[1].header
    #print(h2)
    #return h1

def add_header(meta,header):
    for name,param in meta.items():
        if issubclass(param.__class__, DateParameter):
            value=param.value.isoutc()
            if debug:
                print('time',value)
            kw=getFitsKw(name)
            #__import__('pdb').set_trace()
            header[kw]=(value,param.description)
        elif issubclass(param.__class__, NumericParameter):
            if issubclass(param.value.__class__, Vector):
                for i, com in enumerate(param.value.components):
                    kw=getFitsKw(name,1)+str(i)
                    header[kw]=(com,param.description+str(i))
                    if debug:
                        print(kw,com)
            else:
                    kw=getFitsKw(name)
                    header[kw]=(param.value,param.description)
        elif issubclass(param.__class__, StringParameter):
            kw=getFitsKw(name)
            v= param.value if param.value is not None else ''
            header[kw]=(v,param.description)
        elif issubclass(param.__class__, BooleanParameter):
            kw=getFitsKw(name)
            v='T' if param.value else 'F'
            header[kw]=(v,param.description)
        else:
            kw=getFitsKw(name)
            v=''
            header[kw]=(v,'%s of unknown type' % str(param.value))
    if debug:
        print('***',header)
    return header
   
def fits_header():
    fitsdir = '/Users/jia/desktop/vtse_out/'
    f=fits.open(fitsdir + 'array.fits')
    h=f[0].header
    #h.set('add','header','add a header')
    h['add']=('header','add a header')
    h['test']=('123','des')
    f.close()
    
    return h    
    
def test_fits_kw(h):
    #print(h)
    print(list(h.keys()))
    #assert FITS_KEYWORDS['CUNIT'] == 'cunit'
    assert getFitsKw(list(h.keys())[0]) == 'SIMPLE'
    assert getFitsKw(list(h.keys())[3]) == 'NAXIS1'

if __name__ == '__main__':

    #test_fits_kw(fits_data())
    main()
