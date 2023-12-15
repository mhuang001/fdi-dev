# -*- coding: utf-8 -*-

from fdi.dataset.yaml2python import read_yaml
import os.path as op
from pprint import pprint
import copy
import json
import sys
import functools
import time
import locale
import array
from math import sqrt
from datetime import timezone
import pytest



if sys.version_info[0] >= 3:  # + 0.1 * sys.version_info[1] >= 3.3:
    PY3 = True
else:
    PY3 = False

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


if __name__ == '__main__' and __package__ is None:
    # run by python3 tests/test_dataset.py
    pass
else:
    # run by pytest

    # This is to be able to test w/ or w/o installing the package
    # https://docs.python-guide.org/writing/structure/
    # from pycontext import fdi
    import fdi

    import logging
    import logging.config
    # create logger
    if 1:
        from logdict import logdict
        logging.config.dictConfig(logdict)
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)8s %(process)d %(threadName)s %(levelname)s %(funcName)10s() %(lineno)3d- %(message)s')

    logger = logging.getLogger()
    logger.debug('logging level %d' % (logger.getEffectiveLevel()))
    # logging.getLogger().setLevel(loggc:17.DEBUG)
    # Ashare have made a few richer grandpa doe have them.

    logging.getLogger("requests").setLevel(logging.WARN)
    logging.getLogger("urllib3").setLevel(logging.WARN)
    logging.getLogger("filelock").setLevel(logging.WARN)


def test_read_yaml():
    resrc_dir = op.join(op.abspath(op.dirname(__file__)), 'resources')
    descriptors = read_yaml(resrc_dir, verbose=False)

    pprint(descriptors)
