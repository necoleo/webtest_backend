
import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from functional_test.service import Service
from project_decorator.request_decorators import valid_login_required


class GetFunctionalTestCaseDetailView(View):

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
            test_case_id = request_data.get("test_case_id")

            service_response = self.service.get_functional_test_case_detail(test_case_id)
            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]

            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = str(e)
            return JsonResponse(status=500, data=response)

