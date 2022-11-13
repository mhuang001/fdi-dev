# -*- coding: utf-8 -*-

""" from https://stackoverflow.com/a/70797664  reubano"""

from .namespace import NameSpace_meta, refloader
from ..utils.common import find_all_files, trbk

#from jsonschema import Draft7Validator as the_validator
from jsonschema import Draft201909Validator as the_validator
from jsonschema import RefResolver
from jsonschema.exceptions import RefResolutionError

import json
import os
import copy
from collections import ChainMap
import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))

FDI_SCHEMA_BASE = 'https://fdi.schemas'

FDI_SCHEMA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../schemas'))
""" The directory where the schema definition files are stored."""

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

    if schema_dir is None:
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
    store = dict((schema.get("$id",schema.get("id")), schema) for schema in schemas)

    return store


def schema_dir_loader(key, mapping, remove=True,
                      exclude=None, ignore_error=False,
                      verbose=False):
    """ load all schemas in the given directory and its subdirs. """

    if exclude is None:
        exclude = []

    if key is None:
        return {}

    res = {}

    spath, sname = tuple(key.rsplit('/', 1))
    family = (x for x in mapping if x not in exclude and x.startswith(spath))
    for sch in family:
        jsn = json.load(sch)
        if jsn is None:
            if ignore_error:
                continue
            else:
                raise ValueError(sch)
        else:
            res[sch] = jsn
            del mapping[sch]
    return res


class Schemas(metaclass=NameSpace_meta,
              sources=[makeSchemaStore(FDI_SCHEMA_DIR)],
              load=refloader
              ):
    pass


def getValidator(schema, schemas=None, schema_store=None, base_schema=None, verbose=False):
    """ Returns a `jsonschema` validator that knows where to find given schemas.

    :schema: the schema this validator is made for.
    :schemas: A map of schema id and schema objects. default is all schemas found in ```schema_store```. If it has '$schema' and '$id' as keys, it will be the lone schema to be validated against by the returned validator.
    :schema_store: get schemas here if ```schemas``` is ```None```. default is `FDI_SCHEMA_STORE`.
    :base_schema: A reference schema object providing BaseURI. Default is `schema_store[FDI_SCHEMA_BASE]`, whereas the `schema_store` is made with `FDI_SCHEMA_STORE` and `schemas`.
    """

    if issubclass(schema.__class__, str):
        schema = json.loads(schema)
    the_validator.check_schema(schema)
    if issubclass(schemas.__class__, dict) and '$schema' in schemas and '$id' in schemas:
        store = {schemas['$id']: schemas}
    else:
        if schemas is None:
            schemas = {}
        if schema_store is None:
            schema_store = Schemas.mapping
        store = schema_store.add_ns(schemas, 0) if schemas else schema_store
    if verbose:
        print('Schema store:', list(store))
    if base_schema is None:
        # json.load(open("schema/dir/extend.schema.json"))
        #resolver = RefResolver(schema['$id'], store=store, referrer=schema)
        if FDI_SCHEMA_BASE not in store:
            raise ValueError(
                'Base schema is not given and FDI_SCHEMA_BASE %s is not in store.' % FDI_SCHEMA_BASE)
        base_schema = store[FDI_SCHEMA_BASE]
    resolver = RefResolver.from_schema(base_schema, store=store)

    if verbose:
        print('Schema resolver:', resolver)
    validator = the_validator(schema, resolver=resolver)

    return validator


def validateJson(data, validator):
    """ validates a JSON object.

    :data: a JSON object or a _file_full_path that ends with 'json' or 'jsn'.
    """

    if issubclass(data.__class__, str) and \
       (data.endswith('.jsn') or data.endswith('.json')):
        instance = json.load(open(data))
    else:
        instance = data
    try:
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    except RefResolutionError as e:
        logger.error(e)
    return errors


class Schmas(ChainMap):
    def __init__(self, **kwds):

        makeSchemaStore()
