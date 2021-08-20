from http import HTTPStatus
from flask import Blueprint, jsonify
from flasgger import swag_from
from fdi.httppool.model.welcome import WelcomeModel, returnSomething
from fdi.httppool.schema.result import return_specs_dict, return_specs_dict2
from fdi.dataset.serializable import serialize

home_api = Blueprint('hp', __name__)


@home_api.route('/1')
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


home_api2 = Blueprint('hp2', __name__)


@home_api2.route('/2')
@swag_from('swagger.yml')
def welcome2():
    """
    1 liner about the route
    A more detailed description of the endpoint
    ---
    """
    #result = WelcomeModel()
    # return serialize(result), 200

    result = returnSomething()
    return jsonify(result), 200
