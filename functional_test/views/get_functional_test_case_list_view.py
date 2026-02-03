
import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from functional_test.service import Service
from project_decorator.request_decorators import valid_login_required


class GetFunctionalTestCaseListView(View):

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(["GET"]))
    def get(self, request):

        response = {
            "code": "",
            "message": "",
            "data": {}
        }

        try:
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 20))
            test_case_id = request.GET.get("test_case_id")
            if test_case_id is not None:
                test_case_id = int(test_case_id)
            project_id = request.GET.get("project_id")
            if project_id is not None:
                project_id = int(project_id)
            case_title = request.GET.get("case_title")
            module = request.GET.get("module")
            priority = request.GET.get("priority")
            if priority is not None:
                priority = int(priority)
            case_source = request.GET.get("case_source")
            if case_source is not None:
                case_source = int(case_source)
            requirement_id = request.GET.get("requirement_id")
            if requirement_id is not None:
                requirement_id = int(requirement_id)
            execution_status = request.GET.get("execution_status")
            if execution_status is not None:
                execution_status = int(execution_status)

            service_response = self.service.get_functional_test_case_list(page, page_size, test_case_id, project_id, case_title,
                                                                          module, priority, case_source, requirement_id, execution_status)

            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]

            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = str(e)
            return JsonResponse(status=500, data=response)

