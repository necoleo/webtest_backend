import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from requirements.service import Service


class AuditRequirementView(View):

    def __init__(self):
        self.service = Service()

    @method_decorator(require_http_methods(["POST"]))
    def post(self, request):
        """
        提交需求项审核接口
        """
        response = {
            "code": "",
            "message": "",
            "data": {}
        }
        try:
            request_data = json.loads(request.body)
            requirement_id_list = request_data.get("requirement_id_list")

            service_response = self.service.audit_requirement(requirement_id_list)

            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]
            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = str(e)
            return JsonResponse(status=500, data=response)
