# -*- coding: utf-8 -*-

""" from https://stackoverflow.com/a/70797664  reubano"""

import json


from jsonschema import Draft7Validator, RefResolver
from jsonschema.exceptions import RefResolutionError
from .common import find_all_files, trbk

import os
import copy
from collections import ChainMap
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

FDI_SCHEMA_BASE = 'https://fdi.net/schemas'

FDI_SCHEMA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../schemas'))
""" The directory where the schema definition files are stored."""

FDI_SCHEMA_STORE = None
""" The id-obj map for package-wide schemas. To be updated by `makeSchemaStore` when it runs for the first time."""


def makeSchemaStore(schema_dir=None, verbose=False):
    """make a mapping of schema id and schema obj loaded from the given directory.

    Parameters
    ----------
    schema_dir : str
        Name of a directory containing schema definitions in JSON files
    and subdirectories. If is `None` set to `FDI_SCHEMA_DIR`.
    verbose : bool
        Say more if set.

    Returns
    -------
    dict
        file paths vs. schema objects

    Raises
    ------
    # raise ValueError

    """
    global FDI_SCHEMA_STORE

    if schema_dir is None:
        if FDI_SCHEMA_STORE:
            return copy.deepcopy(FDI_SCHEMA_STORE)
        # make package schemas list
        schema_dir = FDI_SCHEMA_DIR

    dirs = find_all_files(schema_dir, verbose=verbose,
                          include='**/*.js*n',
                          exclude=(''),
                          absdir=True)

    schemas = []
    for source in dirs:
        try:
            with open(source, 'r') as f:
                schemas.append(json.load(f))
        except json.decoder.JSONDecodeError as e:
            logger.warning('Cannot load schema %s. No Skipping...' % source)
            logger.warning(trbk(e))
            raise
    store = dict((schema["$id"], schema) for schema in schemas)

    if os.path.abspath(schema_dir) == FDI_SCHEMA_DIR:
        FDI_SCHEMA_STORE = copy.deepcopy(store)

    return store


def getValidator(schema, schemas=None, schema_store=None, base_schema=None, verbose=False):
    """ Returns a `jsonschema` validator that knows where to find given schemas.

    :schema: the schema this validator is made for.
    :schemas: A map of schema id and schema objects. default is all schemas found in ```schema_store```. If it has '$schema' and '$id' as keys, it will be the lone schema to be validated against by the returned validator.
    :schema_store: get schemas here if ```schemas``` is ```None```. default is `FDI_SCHEMA_STORE`.
    :base_schema: A reference schema object providing BaseURI. Default is `schemas["...base.schema"]`.
    """
    if issubclass(schema.__class__, str):
        schema = json.loads(schema)
    Draft7Validator.check_schema(schema)
    if issubclass(schemas.__class__, dict) and '$schema' in schemas and '$id' in schemas:
        store = {schemas['$id']: schemas}
    else:
        if schemas is None:
            schemas = {}
        if schema_store is None:
            schema_store = makeSchemaStore()
        store = ChainMap(schemas, schema_store)

    if verbose:
        print('Schema store:', list(store))
    if base_schema is None:
        # json.load(open("schema/dir/extend.schema.json"))
        base_schema = store[FDI_SCHEMA_BASE]
    resolver = RefResolver.from_schema(base_schema, store=store)

    if verbose:
        print('Schema resolver:', resolver)
    validator = Draft7Validator(schema, resolver=resolver)

    return validator


def validateJson(data, validator):
    """ validates a JSON object.

    :data: a JSON object or a _file_full_path that ends with 'json' or 'jsn'.
    """

    if data.endswith('.jsn') or data.endswith('.json'):
        instance = json.load(open(data))
    else:
        instance = data
    try:
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    except RefResolutionError as e:
        print(e)
