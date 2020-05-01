# -*- coding: utf-8 -*-

# Automatically generated from fdi/dataset/resources/Product.yml. Do not edit.

from collections import OrderedDict
from fdi.dataset.baseproduct import BaseProduct
from fdi.dataset.finetime import FineTime1



import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


class Product(BaseProduct):
    """ Product class (level ALL) version 0.3 inheriting baseProduct. Automatically generated from fdi/dataset/resources/Product.yml on 2020-05-01 21:18:58.010098.

    Generally a Product (inheriting BaseProduct) has project-wide attributes and can be extended to define a plethora of specialized products.
    """

    productInfo = {
        'metadata': OrderedDict({
            'description': {
                'data_type': 'string',
                'description': 'Description of this product',
                'unit': '',
                'default': 'UNKOWN',
            },
            'type': {
                'data_type': 'string',
                'description': 'Product Type identification. Fully qualified Python class name or CARD.',
                'unit': 'None',
                'default': 'Product',
            },
            'creator': {
                'data_type': 'string',
                'description': 'Generator of this product. Example name of institute, organization, person, software, special algorithm etc.',
                'unit': '',
                'default': 'UNKOWN',
            },
            'creationDate': {
                'data_type': 'finetime',
                'description': 'Creation date of this product',
                'unit': '',
                'default': '0',
            },
            'rootCause': {
                'data_type': 'string',
                'description': 'Reason of this run of pipeline.',
                'unit': '',
                'default': 'UNKOWN',
            },
            'schema': {
                'data_type': 'string',
                'description': 'Version of product schema',
                'unit': 'None',
                'default': '0.3',
            },
            'startDate': {
                'data_type': 'finetime',
                'description': 'Nominal start time  of this product.',
                'unit': 'None',
                'default': '0',
            },
            'endDate': {
                'data_type': 'finetime',
                'description': 'Nominal end time  of this product.',
                'unit': 'None',
                'default': '0',
            },
            'instrument': {
                'data_type': 'string',
                'description': 'Instrument that generated data of this product',
                'unit': 'None',
                'default': 'UNKOWN',
            },
            'modelName': {
                'data_type': 'string',
                'description': 'Model name of the instrument of this product',
                'unit': 'None',
                'default': 'UNKOWN',
            },
            'mission': {
                'data_type': 'string',
                'description': 'Name of the mission.',
                'unit': 'None',
                'default': 'SVOM',
            },
        }),
    }



    def __init__(self,
                 description = 'UNKOWN',
                 type_ = 'Product',
                 creator = 'UNKOWN',
                 creationDate = FineTime1(0),
                 rootCause = 'UNKOWN',
                 schema = '0.3',
                 startDate = FineTime1(0),
                 endDate = FineTime1(0),
                 instrument = 'UNKOWN',
                 modelName = 'UNKOWN',
                 mission = 'SVOM',
                 **kwds):
        """ Initializes instances with more metadata as attributes, set to default values.

        Put description keyword argument here to allow 'BaseProduct("foo") and description='foo'
        """

        if 'metasToBeInstalled' not in kwds:
            # this class is being called directly

            # list of local variables.
            lvar = locals()
            lvar.pop('self')
            lvar.pop('__class__')
            lvar.pop('kwds')
            metasToBeInstalled = lvar
        else:
            # This class is being called probably from super() in a subclass
            metasToBeInstalled = kwds['metasToBeInstalled']
            del kwds['metasToBeInstalled']


# must be the first line to initiate meta and get description
        super(Product , self).__init__(
            metasToBeInstalled=metasToBeInstalled, **kwds)

        #self.installMetas(lvar=lvar)
        #print('% ' + self.meta.toString())
