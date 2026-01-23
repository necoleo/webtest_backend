from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from project_decorator.request_decorators import valid_login_required


class ParseRequirementDocumentView(View):

    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        """
        解析需求文档，将需求文档解析成一条一条的需求项
        :param request:
        :return:
        """