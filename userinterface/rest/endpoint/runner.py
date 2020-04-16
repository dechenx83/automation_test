from flask_restplus import Namespace, reqparse, Resource
from flask import make_response, jsonify
from controller.manager import *
import os

name_space = Namespace("case-runner", description="Case Runner")

runner_param = reqparse.RequestParser()
runner_param.add_argument("status", required=True, type=str, location="json")
runner_param.add_argument("setting_path", required=False, type=str, location="json")

test_list_param = reqparse.RequestParser()
test_list_param.add_argument("file", required=True, type=str, location="json")

resource_param = reqparse.RequestParser()
resource_param.add_argument("file", required=True, type=str, location="json")
resource_param.add_argument("user", required=True, type=str, location="json")


def _get_response(result, message, code):
    return make_response(jsonify({"Result": result, "Message": message}), code)


@name_space.route("")
class CaseRunnerApi(Resource):

    @name_space.expect(runner_param)
    @name_space.response(202, "Case Start Running")
    @name_space.response(400, "Wrong Parameters")
    def put(self):
        arg = runner_param.parse_args()
        if arg['status'].lower() == "start":
            run_test()
            return _get_response(True, "Test Started", 202)
        elif arg['status'].lower() == "init":
            init_engine()
            load_settings(arg['setting_path'])
            return _get_response(True, "Test Runner Initialized", 200)
        else:
            return _get_response(False, "Unknown Status", 400)


@name_space.route("/testlist")
class TestListApi(Resource):

    @name_space.response(200, "Load Test List")
    @name_space.response(400, "Wrong Parameters")
    @name_space.response(500, "Error")
    @name_space.expect(test_list_param)
    def put(self):
        arg = test_list_param.parse_args()
        if not os.path.exists(arg['file']):
            return _get_response(False, "Test List not found", 500)
        try:
            load_test_list(arg['file'])
            return _get_response(True, "Test List loaded", 200)
        except Exception as ex:
            return _get_response(False, str(ex), 500)

    @name_space.response(200, "Test List")
    @name_space.response(500, "Error")
    def get(self):
        return make_response(jsonify(get_test_list()), 200)


@name_space.route("/resource")
class TestResourceApi(Resource):

    @name_space.response(200, "Test Resource Loaded")
    @name_space.response(400, "Wrong Parameters")
    @name_space.response(500, "Error")
    @name_space.expect(resource_param)
    def put(self):
        arg = resource_param.parse_args()
        if not os.path.exists(arg['file']):
            return _get_response(False, "Resource File", 500)
        try:
            load_resource(arg['file'], arg["user"])
            return _get_response(True, "Test Resource loaded", 200)
        except Exception as ex:
            return _get_response(False, str(ex), 500)

