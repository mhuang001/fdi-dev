# -*- coding: utf-8 -*-

from fdi.dataset.finetime import FineTime1
from fdi.dataset.baseproduct import BaseProduct
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


# -*- coding: utf-8 -*-

# Automatically generated from Mandatory.yml. Do not edit.

#import datetime


class Product(BaseProduct):
    """ A Product is a generic result that can be passed on between
    (standalone) processes.

    In general a Product contains zero or more datasets, history,
    optional metadata as well as some required metadata fields.
    Its intent is that it can fully describe itself; this includes
    the way how this product was achieved (its history). As it is
    the result of a process, it should be able to save to and restore
    from an Archive device.

    Many times a Product may contain a single dataset and for this
    purpose the first dataset entry can be accessed by the getDefault()
    method. Note that the datasets may be a composite of datasets
    by themselves.

    mh: Mandatory Attributes can be accessed with e.g. p.creator
    or p.meta['creator']
    """

    projectinfo = {
        'metadata': {
            'mission': {
                'data_type': 'string',
                'description': 'Name of the mission.',
                'default': 'SVOM',
            },
            'instrument': {
                'data_type': 'string',
                'description': 'Instrument that generated data of this product',
                'default': 'UNKOWN',
            },
            'modelName': {
                'data_type': 'string',
                'description': 'Model name of the instrument of this product',
                'default': 'UNKOWN',
            },
        },
    }

    def __init__(self,
                 instrument=None,
                 startDate=None,
                 endDate=None,
                 modelName=None,
                 mission=None,
                 **kwds):
        """ initializes with more metadata as attributes.
        """

        # must be the first line to initiate meta and get description
        super(Product, self).__init__(**kwds)

        # list of local variables. 'description' has been consumed in
        # in annotatable super class so it is not in.
        lvar = locals()
        lvar.pop('self')

        self.installMetas(group=Product.projectinfo['metadata'], lvar=lvar)
        #print('% ' + self.meta.toString())
