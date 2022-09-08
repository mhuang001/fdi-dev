# -*- coding: utf-8 -*-

# Automatically generated from fdi/dataset/resources/TableDataset_DataModel.yml. Do not edit.

from collections import OrderedDict
from builtins import str
from builtins import list


import copy

import logging
# create logger
logger = logging.getLogger(__name__)


# Data Model specification for mandatory components
_Model_Spec = {
    'name': 'TableDataset_DataModel',
    'description': 'TableDataset class data model mandatory configuration',
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
        'type': {
                'data_type': 'string',
                'description': 'Data Type identification.',
                'default': 'TableDataset',
                'valid': '',
                },
        'shape': {
                'data_type': 'list',
                'description': 'Number of columns and rows.',
                'default': [],
                'valid': '',
                },
        'version': {
                'data_type': 'string',
                'description': 'Version of dataset',
                'default': '0.3',
                'valid': '',
                },
        'FORMATV': {
                'data_type': 'string',
                'description': 'Version of dataset schema and revision',
                'default': '1.6.0.3',
                'valid': '',
                },
        },
    'datasets': {
        },
    }

Model = copy.deepcopy(_Model_Spec)
