import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from api_auto_test.service import Service
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required


class UpdateApiTestEnvironmentView(View):
    """
    更新接口测试环境配置
    """

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        """
        更新接口测试环境配置接口
        :param
        request: {
            "environment_id": "integer",
            "env_name": "string",
            "base_url": "string",
            "description": "string",
            "timeout": "integer",
            "headers": "object",
            "variables": "object",
            "is_default": "boolean"
        }
        :return:
        """

        response = {
            "code": "",
            "message": "",
            "data": {}
        }

        try:
            request_data = json.loads(request.body)
            environment_id = request_data.get("environment_id")
            env_name = request_data.get("env_name")
            base_url = request_data.get("base_url")
            description = request_data.get("description")
            timeout = request_data.get("timeout")
            headers = request_data.get("headers")
            variables = request_data.get("variables")
            is_default = request_data.get("is_default")

            service_response = self.service.update_api_test_environment(
                environment_id, env_name, base_url, description,
                timeout, headers, variables, is_default
            )
            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]

            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)
