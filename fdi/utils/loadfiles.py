# -*- coding: utf-8 -*-

from fdi.dataset.mediawrapper import MediaWrapper

import os.path as op
import logging
# create logger
logger = logging.getLogger(__name__)


def loadcsv(filepath, delimiter=',', header=0, return_dict=False):
    """ Loads the contents of a CSV file into a list of tuples.

    :header: the first header linea are taken as column headers if ```header > 0```. If no column header given (default 0), ```colN``` where N = 1, 2, 3... are returned.

    the second header linea are also recorded (usually units) if `header ` > 1.
    :return_dict: if ```True``` returns ```dict[colhd]=(col, unit). Default is ```False```.

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
                for col, cell in zip(columns, row):
                    col.append(cell)
            #print('%d: %s' % (rowcount, str(row)))
            rowcount += 1
    if colhds is None:
        return {} if return_dict else []
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
