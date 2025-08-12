from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from projects.project_service import ProjectService


class ShowProjectView(View):

    service = ProjectService()

    @method_decorator(require_http_methods(['GET']))
    def get(self, request):

        response = self.service.get_projects_list()

        return JsonResponse(status=200, data=response)

