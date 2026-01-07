import json

from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

from api_auto_test.service import Service
from project_decorator.request_decorators import valid_login_required


class ParseApiDocumentView:
    """
    解析需求文档接口
    """
    def __init__(self):
        self.service = Service()

    """
    上传接口文档
    """
    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods("POST"))
    def post(self, request):

        response = {
            "code": "",
            "message": "",
            "data": {},
        }

        try:
            request_data = json.loads(request.body)



            service_response = self.service