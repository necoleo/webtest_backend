import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from functional_test.service import Service
from project_decorator.request_decorators import valid_login_required


class UpdateFunctionalTestCaseView(View):

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(["POST"]))
    def post(self, request):

        response = {
            "code": "",
            "message": "",
            "data": {}
        }

        try:
            request_data = json.loads(request.body)
            test_case_id = request_data.get("test_case_id")
            case_title = request_data.get("case_title")
            precondition = request_data.get("precondition")
            test_steps = request_data.get("test_steps")
            expected_result = request_data.get("expected_result")
            module = request_data.get("module")
            priority = request_data.get("priority")
            comment = request_data.get("comment")
            execution_status = request_data.get("execution_status")

            service_response = self.service.update_functional_test_case(test_case_id, case_title, precondition,
                                    test_steps, expected_result, module, priority,
                                    comment, execution_status)

            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]

            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = str(e)
            return JsonResponse(status=500, data=response)
