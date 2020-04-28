# -*- coding: utf-8 -*-

# Automatically generated from /cygdrive/d/code/fdi/fdi/dataset/resources/Product.yml. Do not edit.

# import datetime
from fdi.dataset.finetime import FineTime1
from fdi.dataset.baseproduct import BaseProduct


import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Product(BaseProduct):
    """ A Product is a BaseProduct that has project-wide attributes and can be extended to define a plethora of pecialized products.
    """

    projectinfo = {
        'metadata': {
            'type': {
                'data_type': 'string',
                'description': 'Product Type identification. Fully qualified Python class name or CARD.',
                'unit': '',
                'default': 'Product',
            },
            'startDate': {
                'data_type': 'finetime',
                'description': 'Nominal start time  of this product.',
                'unit': '',
                'default': FineTime1(0),
            },
            'endDate': {
                'data_type': 'finetime',
                'description': 'Nominal end time  of this product.',
                'unit': '',
                'default': FineTime1(0),
            },
            'instrument': {
                'data_type': 'string',
                'description': 'Instrument that generated data of this product',
                'unit': '',
                'default': 'UNKOWN',
            },
            'modelName': {
                'data_type': 'string',
                'description': 'Model name of the instrument of this product',
                'unit': '',
                'default': 'UNKOWN',
            },
            'mission': {
                'data_type': 'string',
                'description': 'Name of the mission.',
                'unit': '',
                'default': 'SVOM',
            },
        },
    }


    def __init__(self,
                 type_ = None,
                 startDate = None,
                 endDate = None,
                 instrument = None,
                 modelName = None,
                 mission = None,
                 **kwds):
        """ initializes with more metadata as attributes.
        """

        # must be the first line to initiate meta and get description
        super(Product , self).__init__(**kwds)

        # list of local variables. 'description' has been consumed in
        # in annotatable super class so it is not in.
        lvar = locals()
        lvar.pop('self')

        self.installMetas(group=Product.projectinfo['metadata'], lvar=lvar)
        #print('% ' + self.meta.toString())
