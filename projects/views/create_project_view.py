import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required
from projects.service import Service


class CreateProjectView(View):
    """
    创建项目接口
    """
    def __init__(self):
        self.service = Service()

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods("POST"))
    def post(self, request):
        response = {
            "code": "",
            "message": "",
            "data": {}
        }

        try:
            project_params_dict = json.loads(request.body)
            project_params_dict["created_user_id"] = request.user.id
            project_params_dict["created_username"] = request.user.username

            service_response = self.service.create_project(project_params_dict)
            response['code'] = service_response['code']
            response['message'] = service_response['message']
            response['data'] = service_response['data']

            return JsonResponse(status=service_response['status_code'], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)