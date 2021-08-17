return_specs_dict = {
    "parameters": [
        {
            "name": "palette",
            "in": "path",
            "type": "string",
            "enum": [
                "all",
                "rgb",
                "cmyk"
            ],
            "required": "true",
            "default": "all"
        }
    ],
    "definitions": {
        "Palette": {
            "type": "object",
            "properties": {
                "palette_name": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Color"
                    }
                }
            }
        },
        "Color": {
            "type": "string"
        },
        "ReturnSchema": {
            "type": "object",
            "properties": {
                "result": {
                    "$ref": "#/definitions/Ret_Result"
                },
                "msg": {
                    "$ref": "#/definitions/Ret_Message"
                },
                "time": {
                    "$ref": "#/definitions/Ret_Timestamp"
                },
            }
        },
        "Ret_Result": {
            "type": "string"
        },
        "Ret_Message": {
            "type": "string"
        },
        "Ret_Timestamp": {
            "type": "float"
        },
    },
    "responses": {
        "200": {
            "description": "A serialized result object, a message string, a floating point timestamp",
            "schema": {
                "$ref": "#/definitions/ResultSchema"
            },
            "examples": {
                "rgb": [
                    "red",
                    "green",
                    "blue"
                ]
            }
        }
    }
}

return_specs_dict2 = {
    "definitions": {
        "ReturnSchema": {
            "type": "object",
            "properties": {
                "result": {
                    "$ref": "#/definitions/Ret_Result"
                },
                "msg": {
                    "$ref": "#/definitions/Ret_Message"
                },
                "time": {
                    "$ref": "#/definitions/Ret_Timestamp"
                },
            }
        },
        "Ret_Result": {
            "type": "string"
        },
        "Ret_Message": {
            "type": "string"
        },
        "Ret_Timestamp": {
            "type": "float"
        },
    },
    "responses": {
        "200": {
            "description": "A serialized result object, a message string, a floating point timestamp",
            "schema": {
                "$ref": "#/definitions/ReturnSchema"
            },
            "examples": {
                'result': '42',
                'msg': 'bar',
                'ts': 9876.543210
            }
        }
    }
}
