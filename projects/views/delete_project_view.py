from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from projects.project_service import ProjectService


class DeleteProjectView(View):
    project_service = ProjectService()

    @method_decorator(require_http_methods(['POST']))
    def post(self, request):

