import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from projects.project_service import ProjectService


class EditProjectView(View):

    service = ProjectService()

    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        response = {}
        status = 400
        request_data = json.loads(request.body)
        project_code = request_data['project_code']
        update_data = request_data['update_data']

        if not project_code:
            response['code'] = "error"
            response['message'] = "缺少必填参数：project_code"
            response['data'] = ""
            return JsonResponse(status=status, data=response)
        if not update_data:
            response['code'] = "error"
            response['message'] = "缺少更新数据：update_data不能为空"
            response['data'] = ""
            return JsonResponse(status=status, data=response)

        response = self.service.update_project_by_code(project_code, update_data)

        if response['code'] == 'success':
            status = 200
        else:
            if '项目不存在' in response['message']:
                status = 404

        return JsonResponse(status=status, data=response)