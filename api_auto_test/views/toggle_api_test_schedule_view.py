import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from api_auto_test.service import Service
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required


class ToggleApiTestScheduleView(View):
    """
    启用/禁用接口测试定时任务
    """

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        """
        启用/禁用接口测试定时任务接口
        :param
        request: {
            "schedule_id": "integer",
            "is_enabled": "boolean"
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
            schedule_id = request_data.get("schedule_id")
            is_enabled = request_data.get("is_enabled")

            service_response = self.service.toggle_api_test_schedule(schedule_id, is_enabled)
            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]

            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)
