import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods
from projects.project_service import ProjectService


class AddProjectView(View):
    service = ProjectService()

    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        request_data = json.loads(request.body)
        status = 400
        response = self.service.add_project(request_data)
        if response['code'] == "success":
            status = 200

        return JsonResponse(status=status, data=response)
