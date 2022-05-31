# -*- coding: utf-8 -*-

""" from https://stackoverflow.com/a/70797664  reubano"""

import json


from jsonschema import Draft7Validator, RefResolver
from jsonschema.exceptions import RefResolutionError
from .common import find_all_files

import os


def getValidator(schema, schemas=None, schema_dir=None, base_schema=None, verbose=False):
    """ Returns a `jsonschema` validator that knows where to find given schemas.

    :schema: the schema this validator is made for.
    :schemas: A list of schema objects. if given is a `dict` it is taken as a lone input schema object. default is all schemas found in files in ```schema_dir```.
    :schema_dir: get schemas here if ```schemas``` is ```None```.
    :base_schema: A reference schema object providing BaseURI. Default is `schemas["...base.schema"]`.
    """

    if schemas is None:
        if schema_dir is None:
            raise ValueError(
                '`schema_dir` cannot be None when `schemas` is None.')
        schemas = list(json.load(open(source))
                       for source in find_all_files(schema_dir, verbose=verbose,
                                                    include='**/*.js*n',
                                                    exclude=('')))
    elif issubclass(schemas.__class__, dict):
        schemas = [schemas]
    schema_store = {schema["$id"]: schema for schema in schemas}

    if verbose:
        print('Schema store:', list(schema_store.keys()))
    if base_schema is None:
        # json.load(open("schema/dir/extend.schema.json"))
        base_schema = schema_store["/schemas/base"]
    resolver = RefResolver.from_schema(base_schema, store=schema_store)
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
