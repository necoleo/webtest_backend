from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required
from requirements.service import Service


class GetRequirementDocumentOptionsView(View):

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(['GET']))
    def get(self, request):
        """
        获取需求文档列表，仅返回需求文档id、需求文档名称、数量
        """
        response = {
            "code": "",
            "message": "",
            "data": {}
        }

        source = request.GET.get("source")

        try:
            service_response = self.service.get_requirements_document_options(source)
            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]
            return JsonResponse(status=service_response["status_code"], data=response)
        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)