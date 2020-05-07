from collections import OrderedDict
from fdi.dataset.finetime import FineTime1


    productInfo = {
        'metadata': OrderedDict({
            'description': {
                'fits_keyword': 'DESCRIPT',
                'data_type': 'string',
                'description': 'Description of this product',
                'unit': 'None',
                'default': 'UNKOWN',
            },
            'type': {
                'fits_keyword': 'TYPE',
                'data_type': 'string',
                'description': 'Product Type identification. Fully qualified Python class name or CARD.',
                'unit': 'None',
                'default': 'BaseProduct',
            },
            'creator': {
                'fits_keyword': 'CREATOR',
                'data_type': 'string',
                'description': 'Generator of this product. Example name of institute, organization, person, software, special algorithm etc.',
                'unit': 'None',
                'default': 'UNKOWN',
            },
            'creationDate': {
                'fits_keyword': 'DATE',
                'data_type': 'finetime',
                'description': 'Creation date of this product',
                'unit': 'None',
                'default': '0',
            },
            'rootCause': {
                'fits_keyword': 'ROOTCAUS',
                'data_type': 'string',
                'description': 'Reason of this run of pipeline.',
                'unit': 'None',
                'default': 'UNKOWN',
            },
            'schema': {
                'fits_keyword': 'SCHEMA',
                'data_type': 'string',
                'description': 'Version of product schema',
                'unit': 'None',
                'default': '0.3',
            },
        }),
    }


    def __init__(self,
                 description = 'UNKOWN',
                 type_ = 'BaseProduct',
                 creator = 'UNKOWN',
                 creationDate = FineTime1(0),
                 rootCause = 'UNKOWN',
                 schema = '0.3',
                 **kwds):
