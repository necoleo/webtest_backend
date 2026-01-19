from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from api_auto_test.service import Service
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required


class GetApiTestExecutionStatusView(View):
    """
    获取接口测试执行状态
    """

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(["GET"]))
    def get(self, request):
        """
        获取接口测试执行状态接口（用于轮询）
        :param request:
        :return:
        """

        response = {
            "code": "",
            "message": "",
            "data": {}
        }

        try:
            execution_id = int(request.GET.get("execution_id"))

            service_response = self.service.get_api_test_execution_status(execution_id)
            response['code'] = service_response['code']
            response['message'] = service_response['message']
            response['data'] = service_response['data']

            return JsonResponse(status=service_response['status_code'], data=response)

        except (ValueError, TypeError) as e:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = str(e)
            return JsonResponse(status=400, data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)
