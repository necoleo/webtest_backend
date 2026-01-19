import json
from datetime import time

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from api_auto_test.service import Service
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required


class UpdateApiTestScheduleView(View):
    """
    更新接口测试定时任务
    """

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        """
        更新接口测试定时任务接口
        :param
        request: {
            "schedule_id": "integer",
            "task_name": "string",
            "test_case_id": "integer",
            "env_id": "integer",
            "schedule_type": "integer",
            "schedule_time": "string",
            "description": "string",
            "schedule_weekday": "integer"
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
            task_name = request_data.get("task_name")
            description = request_data.get("description")
            test_case_id = request_data.get("test_case_id")
            env_id = request_data.get("env_id")
            schedule_type = request_data.get("schedule_type")
            schedule_time_str = request_data.get("schedule_time")
            schedule_weekday = request_data.get("schedule_weekday")

            # 解析时间字符串
            schedule_time = None
            if schedule_time_str:
                parts = schedule_time_str.split(":")
                schedule_time = time(int(parts[0]), int(parts[1]))

            service_response = self.service.update_api_test_schedule(
                schedule_id, task_name, description, test_case_id,
                env_id, schedule_type, schedule_time, schedule_weekday
            )
            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]

            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)
