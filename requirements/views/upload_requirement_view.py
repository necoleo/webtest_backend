from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from requirements.service import Service


class UploadRequirementView(View):
    """
    上传需求项
    """

    def __init__(self):
        self.service = Service()

    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        """
        上传需求项接口
        :param
        request: {
            "project_id": "integer",
            "requirement_document_id": integer",
            "requirement_title": string, (可选)
            "requirement_content": string,
            "module": string (可选)
        }
        :return:
        """

        response = {
            "code": "",
            "message": "",
            "data": {}
        }

        try:
            project_id = int(request.POST.get("project_id"))
            requirement_document_id = int(request.POST.get("requirement_document_id"))
            requirement_title = request.POST.get("requirement_title")
            requirement_content = request.POST.get("requirement_content")
            module = request.POST.get("module")
            created_user_id = request.user.id
            created_user = request.user.username

            service_response = self.service.upload_requirement(
                project_id, requirement_document_id, requirement_title,
                requirement_content, module, created_user_id, created_user
            )

            response['code'] = service_response['code']
            response['message'] = service_response['message']
            response['data'] = service_response['data']

            return JsonResponse(status=service_response['status_code'], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)
