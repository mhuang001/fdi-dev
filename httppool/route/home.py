from http import HTTPStatus
from flask import Blueprint, jsonify
from flasgger import swag_from
from httppool.model.welcome import WelcomeModel, returnSomething
from httppool.schema.result import return_specs_dict, return_specs_dict2
from fdi.dataset.serializable import serialize

home_api = Blueprint('httppool', __name__)


@home_api.route('/')
@swag_from({
    'responses': {
        HTTPStatus.OK.value: {
            'description': 'Welcome to the Flask Starter Kit',
            'schema': return_specs_dict2
        }
    }
})
def welcome():
    """
    1 liner about the route
    A more detailed description of the endpoint
    ---
    """
    #result = WelcomeModel()
    # return serialize(result), 200

    result = returnSomething()
    return jsonify(result), 200
