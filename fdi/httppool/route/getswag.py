from flasgger.utils import load_from_file  # , __replace_ref
import yaml
import os
from pprint import pprint


def getSwag():

    ypath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../schema'))
    print('************ swagger yaml dir:', ypath)
    # Use a yaml file derefed with swagger-cli bundle -r
    full_doc = load_from_file(os.path.join(ypath, 'pools_resolved.yml'))
    yaml_start = full_doc.find('---')
    swag = yaml.safe_load(full_doc[yaml_start if yaml_start >= 0 else 0:])
    # the following are not needed if merge is set in swagger=Swagger(app,merge=True)
    #swag['specs'] = []
    #swag['headers'] = []

    # this isn't working with e.g. allOf - $ref .. so the yml is a deref'ed
    #swag = __replace_ref(swag, ypath, swag)
    return swag


try:
    s = swag

except NameError:
    swag = getSwag()
