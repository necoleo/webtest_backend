import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from functional_test.service import Service
from project_decorator.request_decorators import valid_login_required


class CreateFunctionalTestCaseView(View):

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
            project_id = request_data.get("project_id")
            requirement_id = request_data.get("requirement_id")
            case_title = request_data.get("case_title")
            test_steps = request_data.get("test_steps")
            expected_result = request_data.get("expected_result")
            precondition = request_data.get("precondition")
            module = request_data.get("module")
            priority = request_data.get("priority")
            comment = request_data.get("comment")
            case_source = request_data.get("case_source")
            created_user_id = request.user.id
            created_user = request.user.username

            service_response = self.service.create_functional_test_case(project_id, requirement_id, case_title, test_steps,
                                                                        expected_result, created_user_id, created_user, precondition,
                                                                        module, priority, comment, case_source)

            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]

            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = str(e)
            return JsonResponse(status=500, data=response)

