import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from api_auto_test.service import Service
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required


class ExecuteApiTestCaseView(View):
    """
    执行接口测试用例
    """

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        """
        执行接口测试用例接口
        :param
        request: {
            "test_case_id": "integer",
            "env_id": "integer"
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
            test_case_id = request_data.get("test_case_id")
            env_id = request_data.get("env_id")
            executed_user_id = request.user.id
            executed_user = request.user.username

            service_response = self.service.execute_api_test_case(
                test_case_id, env_id, executed_user_id, executed_user
            )
            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]

            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)
