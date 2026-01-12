import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from projects.service import Service


class UpdateProjectView(View):
    """
    编辑项目接口
    """
    def __init__(self):
        self.service = Service()

    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        """
        编辑项目接口
        :param request:
        :return:
        """
        response = {
            'code': '',
            'message': '',
            'data': {}
        }
        try:
            project_param_dict = json.loads(request.body)

            service_response = self.service.update_project(project_param_dict)

            response['code'] = service_response['code']
            response['message'] = service_response['message']
            response['data'] = service_response['data']

            return JsonResponse(status=service_response['status_code'], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)
