# -*- coding: utf-8 -*-

import logging
# create logger
logger = logging.getLogger(__name__)


def loadcsv(filepath, delimiter=',', header=0):
    """ Loads the controls of a CSV file into a list of tuples.

    the first header linea are taken as column headers if header > 0.
    if no column header given, colN where N = 1, 2, 3... are returned.

    the second header linea are also recorded (usually units) if header > 1.
    Default is ''.

    Returns of a list of (colhd, column, unit) tuplees.
    """
    columns = []

    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        logger.debug('reading csv file ' + str(f))
        # pdb.set_trace()
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

    return list(zip(colhds, columns, units))
