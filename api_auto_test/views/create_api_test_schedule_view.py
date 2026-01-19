import json
from datetime import time

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from api_auto_test.service import Service
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required


class CreateApiTestScheduleView(View):
    """
    创建接口测试定时任务
    """

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        """
        创建接口测试定时任务接口
        :param
        request: {
            "project_id": "integer",
            "task_name": "string",
            "test_case_id": "integer",
            "env_id": "integer",
            "schedule_type": "integer",  # 0=每天, 1=每周
            "schedule_time": "string",  # "HH:MM" 格式
            "description": "string",
            "schedule_weekday": "integer",  # 1-7
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
            project_id = request_data.get("project_id")
            task_name = request_data.get("task_name")
            test_case_id = request_data.get("test_case_id")
            env_id = request_data.get("env_id")
            schedule_type = request_data.get("schedule_type")
            schedule_time_str = request_data.get("schedule_time")
            description = request_data.get("description")
            schedule_weekday = request_data.get("schedule_weekday")
            is_enabled = request_data.get("is_enabled", True)
            created_user_id = request.user.id
            created_user = request.user.username

            # 解析时间字符串
            if schedule_time_str:
                parts = schedule_time_str.split(":")
                schedule_time = time(int(parts[0]), int(parts[1]))
            else:
                response["code"] = ErrorCode.PARAM_BLANK
                response["message"] = "执行时间不能为空"
                return JsonResponse(status=400, data=response)

            service_response = self.service.create_api_test_schedule(
                project_id, task_name, test_case_id, env_id,
                schedule_type, schedule_time, created_user_id, created_user,
                description, schedule_weekday, is_enabled
            )
            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]

            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)
