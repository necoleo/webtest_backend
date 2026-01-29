
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
            request_data = json.loads(request.body)
            page = request_data.get("page", 1)
            page_size = request_data.get.get("page_size", 20)
            test_case_id = request_data.get("test_case_id")
            project_id = request_data.get("project_id")
            case_title = request_data.get("case_title")
            module = request_data.get("module")
            priority = request_data.get("priority")
            case_source = request_data.get("case_source")
            requirement_id = request_data.get("requirement_id")
            execution_status = request_data.get("execution_status")

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

