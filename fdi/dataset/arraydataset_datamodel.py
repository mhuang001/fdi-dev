# -*- coding: utf-8 -*-

# Automatically generated from fdi/dataset/resources/ArrayDataset_DataModel.yml. Do not edit.

from collections import OrderedDict


from fdi.dataset.readonlydict import ReadOnlyDict

import copy

import logging
# create logger
logger = logging.getLogger(__name__)


# Data Model specification for mandatory components
_Model_Spec = {
    'name': 'ArrayDataset_DataModel',
    'description': 'ArrayDataset class data model mandatory configuration',
    'parents': [
        None,
        ],
    'schema': '1.6',
    'metadata': {
        'description': {
                'data_type': 'string',
                'description': 'Description of this dataset',
                'default': 'UNKNOWN',
                'valid': '',
                },
        'unit': {
                'data_type': 'string',
                'description': 'Unit of every element.',
                'default': None,
                'valid': '',
                },
        'shape': {
                'data_type': 'tuple',
                'description': 'Number of elements in each dimension. Quick changers to the right.',
                'default': (),
                'valid': '',
                },
        'typecode': {
                'data_type': 'string',
                'description': 'Python internal storage code.',
                'default': 'UNKNOWN',
                'valid': '',
                },
        'version': {
                'data_type': 'string',
                'description': 'Version of dataset',
                'default': '0.1',
                'valid': '',
                },
        'FORMATV': {
                'data_type': 'string',
                'description': 'Version of dataset schema and revision',
                'default': '1.6.0.1',
                'valid': '',
                },
        },
    'datasets': {
        },
    }

Model = ReadOnlyDict(_Model_Spec)


