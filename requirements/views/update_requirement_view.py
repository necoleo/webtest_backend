import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from requirements.service import Service


class UpdateRequirementView(View):

    def __init__(self):
        self.service = Service()

    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        """
        编辑需求项接口
        :param request:
        :return:
        """
        response = {
            'code': '',
            'message': '',
            'data': {}
        }
        try:
            request_data = json.loads(request.body)
            requirement_id = request_data['requirement_id']
            requirement_title = request_data['requirement_title']
            requirement_content = request_data['requirement_content']
            module = request_data['module']

            service_response = self.service.update_requirement(requirement_id, requirement_title, requirement_content, module)

            response['code'] = service_response['code']
            response['message'] = service_response['message']
            response['data'] = service_response['data']

            return JsonResponse(status=service_response['status_code'], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)
