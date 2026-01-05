import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from api_auto_test.service import Service
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required


class UploadApiDocumentView(View):

    def __init__(self):
        self.service = Service()

    """
    上传接口文档
    """
    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods("POST"))
    def post(self, request):
        """
        上传接口文档接口
        :param
        request: {
            "project_id": "integer",
            "version": "string",
            "file": "file",
            "comment": "string"
        }
        :return:
        """

        response = {
            "code": "",
            "message": "",
            "data": {}
        }

        try:
            request_data = json.loads(request.body)
            project_id = request_data.get("project_id")
            version = request_data.get("version")
            file = request_data.get("file")
            comment = request_data.get("comment")
            created_user = request.user

            service_response = self.service.upload_api_document(project_id, version, file, comment, created_user)
            response['code'] = service_response['code']
            response['message'] = service_response['message']
            response['data'] = service_response['data']

            return JsonResponse(status=service_response['status_code'], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)





