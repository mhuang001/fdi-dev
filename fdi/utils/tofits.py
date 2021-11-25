from fdi.utils.fits_kw import FITS_KEYWORDS,getFitsKw
from fdi.dataset.arraydataset import ArrayDataset
from fdi.dataset.tabledataset import TableDataset
from fdi.dataset.dataset import CompositeDataset
from fdi.dataset.dataset import Dataset
from fdi.dataset.baseproduct import BaseProduct
from astropy.io import fits

import numpy as np
import os

def main():
    fitsdir = '/Users/jia/desktop/vtse_out/'
    if os.path.exists(fitsdir + 'array.fits'):
        os.remove(fitsdir + 'array.fits')
    ima=ArrayDataset(data=[[1,2,3,4],[5,6,7,8]], description='a')
    imb=ArrayDataset(data=[[1,2,3,4],[5,6,7,8],[1,2,3,4],[5,6,7,8]], description='b')
    #im=[[1,2,3,4],[5,6,7,8]]
    hdul = fits.HDUList()
    fits_dataset(hdul,[ima,imb])

def toFits(data):
    hdul = fits.HDUList()
    hdul.append(fits.PrimaryHDU())
    if issubclass(data[0].__class__, Dataset):
        hdul=fits_dataset(hdul,data)
        print("***",len(hdul))
    elif issubclass(data.__class__, BaseProduct):
        fits_product(hdul,data)
    return hdul

def fits_dataset(hdul,ima_list):
   

    for n, ima in enumerate(ima_list):
        
        print(n)
        header = fits.Header()
        if issubclass(ima.__class__, ArrayDataset):
            a=np.array(ima)
            print (a.shape)
            hdul.append(fits.ImageHDU(a,header=header))
            #header=add_header(a.meta,header)

        elif issubclass(ima.__class__, TableDataset):
            units=[]
            dtype=[]
            data=[getRow(Slice)]
            desc=[]
            for name, col in ima.items():
                units.append(col.unit)
                dtype.append(col.typecode)
                
                desc.append(col.description)
            t=table(name=ima.getColumnNames(units=units, dtype=dtype, data=data))
            
            hdul.append(fits.BinTableHDU(a,header=header))
            #header=add_header(a.meta,header)
            
        elif issubclass(ima.__class__, CompositeDataset):
            dataset=fits_dataset(hdul,ima)
    print("***",len(hdul))
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
        kw=getFitsKw(name)
        header[kw]=(param.value,param.description)
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