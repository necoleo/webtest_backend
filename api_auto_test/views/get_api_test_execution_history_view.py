from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from api_auto_test.service import Service
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required


class GetApiTestExecutionHistoryView(View):
    """
    获取接口测试执行历史记录
    """

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(["GET"]))
    def get(self, request):
        """
        获取接口测试执行历史记录列表接口
        :param request:
        :return:
        """

        response = {
            "code": "",
            "message": "",
            "data": {}
        }

        try:
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 20))
            test_case_id = request.GET.get("test_case_id")
            if test_case_id:
                test_case_id = int(test_case_id)
            project_id = request.GET.get("project_id")
            if project_id:
                project_id = int(project_id)
            status = request.GET.get("status")
            if status:
                status = int(status)
            trigger_type = request.GET.get("trigger_type")
            if trigger_type:
                trigger_type = int(trigger_type)
            has_report = request.GET.get("has_report")
            if has_report:
                has_report = has_report.lower() in ('true', '1', 'yes')

            service_response = self.service.get_api_test_execution_history(
                page, page_size, test_case_id, project_id, status, trigger_type, has_report
            )
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
