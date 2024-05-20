# -*- coding: utf-8 -*-

from .common import trbk
from fdi.dataset.mediawrapper import MediaWrapper

import mmap
import os.path as op
import logging
# create logger
logger = logging.getLogger(__name__)


def get_mmap(filename, start=None, end=None, access=mmap.ACCESS_READ, close=False, alternative=None, error_msg=None):
        """Read a file as mmap and return the buffer as a string.

        Parameters
        ----------
        filename : str
            name of the file.
        start : int
            offset of the start. If set `None` read the whole file.
        end : int
            offset of the end, in bytes.
        access :
            access for mmap. default is `mmap.ACCESS_READ`
        close : bool
            whether to close the time before returning.
        alternative : file object
            use a normal file if passing an open file object inplace of mmap. Pass None otherwise (default).
        error_msg : str
            How would you tell about the error if file cannot be
            read. Default is ``Error in HK reading``.

        Returns
        -------
        tuple
            The buffer decoded to ascii and file_object (could be None)

        Raises
        ------
        KeyError

        """
        
        if error_msg is None:
            error_msg = "Error in HK reading."
        fp = op.abspath(filename)
        try:
            if alternative is None:
                file_obj = open(fp, mode="r+", encoding="utf-8")
                mmap_obj = mmap.mmap(
                    file_obj.fileno(), length=0, access=mmap.ACCESS_READ)
                fo = mmap_obj
            else:
                fo = alternative
            if start is None:
                js = fo.read()
            else:
                fo.seek(start)
                js = fo.read(end - start)
        except Exception as e:
            msg = '%s file: %s. exc: %s trbk: %s.' % (error_msg,
                fp, str(e), trbk(e))
            logging.error(msg)
            raise KeyError(msg)
        if close:
            fo.close()
        return js.decode('ascii'), fo

def loadcsv(filepath, delimiter=',', header=0, return_dict=False, pad=None, set_unit=...):
    """ Loads the contents of a CSV file into a list of tuples.

    :header: the first header linea are taken as column headers if ```header > 0```. If no column header given (default 0), ```colN``` where N = 1, 2, 3... are returned.

    the second header linea are also recorded (usually units) if `header ` > 1.
    :return_dict: if ```True``` returns ```dict[colhd]=(col, unit). Default is ```False```.
    :set_unit: if given a string, it will be set as the unit to all columns; if given a list of strings, they will be used to set unit for the columns as long as the list lasts. if goven `None` return with no unit. default is `...` which leaves units as read.
    :return: Default is a list of (colhd, column, unit) tuplees.
    """
    columns, units = [], []
    colhds = None
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        logger.debug('reading csv file ' + str(f))

        rowcount = 0
        for line in iter(f.readline, ''):
            row = ' '.join(x for x in line.split()).split(delimiter)
            # skip blank lines
            if not any((len(x) for x in row)):
                continue
            try:
                row = [float(x) for x in row]
            except ValueError:
                row = [x.strip() for x in row]
            if rowcount == 0:
                columns = [[] for cell in row]
                ncol = len(columns)
                units = ['' for cell in row]
                if header > 0:
                    colhds = [cell for cell in row]
                else:
                    colhds = ['col%d' % (n+1)
                              for n, cell in enumerate(row)]
            elif rowcount == 1:
                if header > 1:
                    units = [cell for cell in row]
            if rowcount < header:
                pass
            else:
                if len(row) < ncol and pad is not None:
                    row += [pad] * (ncol-len(row))
                for col, cell in zip(columns, row):
                    col.append(cell)
            #print('%d: %s' % (rowcount, str(row)))
            rowcount += 1
    if colhds is None:
        return {} if return_dict else []
    if issubclass(set_unit.__class__, str):
        units = [set_unit] * len(units)
    elif issubclass(set_unit.__class__, list):
        for i, u in enumerate(set_unit):
            if i < len(unit):
                unit[i] = u
                continue
            break
    elif set_unit is None:        
        return dict(zip(colhds, columns)) if return_dict \
            else list(zip(colhds, columns))
        
    return dict(zip(colhds, zip(columns, units))) if return_dict \
        else list(zip(colhds, columns, units))


def loadMedia(filename, content_type='image/png'):
    """

    """
    with open(filename, 'rb') as f:
        image = MediaWrapper(data=f.read(),
                             description='A media file in an array',
                             typ_=content_type)
    image.file = filename

    return image
