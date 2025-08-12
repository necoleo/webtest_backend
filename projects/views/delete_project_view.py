import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from projects.project_service import ProjectService


class DeleteProjectView(View):
    project_service = ProjectService()

    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        response = {}
        request_data = json.loads(request.body)
        project_code = request_data['project_code']
        if not project_code:
            response['code'] = "error"
            response['message'] = "缺少项目编号"
            response['data'] = ""
            return JsonResponse(status=400, data=response)

        response = self.project_service.delete_project(project_code)

        if response['code'] == "success":
            status = 200
        else:
            if "项目不存在" in response['message']:
                status = 404
            else:
                status = 400

        return JsonResponse(status=status, data=response)


