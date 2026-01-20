from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from api_auto_test.service import Service
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required


class UploadApiTestCaseView(View):
    """
    上传接口测试用例
    """

    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods("POST"))
    def post(self, request):
        """
        上传接口测试用例接口
        :param
        request: {
            "project_id": "integer",
            "case_name": "string",
            "file": "file",
            "description": "string"
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
            case_name = request.POST.get("case_name")
            file = request.FILES.get("file")
            description = request.POST.get("description")
            created_user_id = request.user.id
            created_user = request.user.username
            service_response = self.service.upload_api_test_case(
                project_id, case_name, file, created_user_id,
                created_user, description
            )
            print(service_response['message'])
            response['code'] = service_response['code']
            response['message'] = service_response['message']
            response['data'] = service_response['data']

            return JsonResponse(status=service_response['status_code'], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)
