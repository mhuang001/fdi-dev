from collections import OrderedDict
from fdi.dataset.baseproduct import BaseProduct
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
                'default': 'Product',
                'valid': '',
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
            'startDate': {
                'fits_keyword': 'DATE_OBS',
                'data_type': 'finetime',
                'description': 'Nominal start time  of this product.',
                'unit': 'None',
                'default': '0',
                'valid': '',
            },
            'endDate': {
                'fits_keyword': 'DATE_END',
                'data_type': 'finetime',
                'description': 'Nominal end time  of this product.',
                'unit': 'None',
                'default': '0',
                'valid': '',
            },
            'instrument': {
                'fits_keyword': 'INSTRUME',
                'data_type': 'string',
                'description': 'Instrument that generated data of this product',
                'unit': 'None',
                'default': 'UNKOWN',
                'valid': '',
            },
            'modelName': {
                'fits_keyword': 'MODEL',
                'data_type': 'string',
                'description': 'Model name of the instrument of this product',
                'unit': 'None',
                'default': 'UNKOWN',
                'valid': '',
            },
            'mission': {
                'fits_keyword': 'TELESCOP',
                'data_type': 'string',
                'description': 'Name of the mission.',
                'unit': 'None',
                'default': '_AGS',
                'valid': '',
            },
            'version': {
                'fits_keyword': 'VERSION',
                'data_type': 'string',
                'description': 'Version of product schema',
                'unit': 'None',
                'default': '0.5',
                'valid': '',
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
                 mission = '_AGS',
                 version = '0.5',
                 **kwds):
