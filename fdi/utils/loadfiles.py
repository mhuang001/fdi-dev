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

def loadcsv(filepath, delimiter=',', header=0,
            #return_dict=False,
            #pad=None,
            set_unit=...):
    """ Loads the contents of a CSV file into a list of tuples.

    Parameters
    ----------
    header : int
        The first `header` line are taken as column headers, default is 0, for the case where no column header is given in the file, and ```colN``` where N = 1, 2, 3... are returned.
    The `header - 1 (where header > 0)` rows below the first header line are also recorded and concatenated with ' ' into one string as the column head, if `header ` > 1.
    set_unit : str, list, None, ...
        If given a string, it will be set as the unit to all columns; if given a list of strings, they will be used to set unit for the columns as long as the list lasts. if `None` is given, return results with no units in the tuple. If given `...`, units are taken as strings of cells from the first row after header rows, if `headers > 0`; Do the same as `None` if `headers == 0`. Default is `...`. 
    Return
    ------
    list
        Default is a list of (column-head, column, unit) tuples.
    """
    #:return_dict: if ```True``` returns ```dict[colhd]=(col, unit). Default is ```False```.
    columns, units = [], []
    colhds = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        logger.debug('reading csv file ' + str(f))

        rowcount = 0
        colhds_ori = []
        for line in iter(f.readline, ''):
            row = ' '.join(line.split()).split(delimiter)
            # skip blank lines
            if not any((len(x) for x in row)):
                continue
            try:
                row = [float(x) for x in row]
            except ValueError:
                row = [x.strip() for x in row]
                pass
                
            if rowcount == 0:
                # must be the first header line
                if header:
                    for cell in row:
                        columns.append([])
                        units.append('')
                        colhds_ori.append([cell])
                else:
                    # no header. fill columns
                    for cell in row:
                        columns.append([cell])
                ncol = len(columns)
            elif rowcount > 0:
                if rowcount < header:
                    # append cell to col header according to original
                    for col, cell in zip(colhds_ori, row):
                        col.append(cell)
                elif rowcount == header and set_unit is ...:
                    # make units
                    units = [cell for cell in row]
                else:
                    # rolecount > header. this is data.
                    #if len(row) < ncol and pad is not None:
                    #    row += [pad] * (ncol-len(row))
                    for col, cell in zip(columns, row):
                        col.append(cell)
                #print('%d: %s' % (rowcount, str(row)))
            else:
                raise ValueError('csv row count cannot be negative. %d' % rowcount)
            rowcount += 1

    # make col-heads
    if header:
        for n, ho in enumerate(colhds_ori):
            lho = len(ho)
            if lho > 1:
                colhds.append('|'.join(map(str,ho)))
            elif lho == 1:
                colhds.append(str(ho[0]))
            else:
                colhds.append('col%d' % (n+1))
        # print(f'* colhds_ori: {colhds_ori}, data: {columns}, units: {units}')
    else:
        # header == 0
        for n in range(ncol):
            colhds.append('col%d' % (n+1))
        # print(f'** colhds_ori: {colhds_ori}, data: {columns}, units: {units}')
        pass
    # mandatory units
    if set_unit is None:
        units = None
    elif issubclass(set_unit.__class__, str):
        units = [set_unit[:]] * ncol
    elif issubclass(set_unit.__class__, list):
        for i in range(min(len(set_unit), len(unit))):
            units[i] = set_unit[i]
    # print(f'*** colhds_ori: {colhds_ori}, data: {columns}, units: {units}')

    # file is read and line-processed.
        #return {} if return_dict else []
    if set_unit is None:
        return list(zip(colhds, columns))
    elif set_unit is ...:
        # print(f'**** colhds_ori: {colhds_ori}, data: {columns}, units: {units}')
        if header == 0:
            return list(zip(colhds, columns))
        elif len(units) == 0:
            units = [ '' for n in range(ncol)]
            return list(zip(colhds, columns, units))
    # has units
    # print(f'***** colhds_ori: {colhds_ori}, data: {columns}, units: {units}')
    return list(zip(colhds, columns, units))


def loadMedia(filename, content_type='image/png'):
    """

    """
    with open(filename, 'rb') as f:
        image = MediaWrapper(data=f.read(),
                             description='A media file in an array',
                             typ_=content_type)
    image.file = filename

    return image
