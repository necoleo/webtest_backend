import json
import re

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from users.service import UserService


# Create your views here.
class UserLoginView(View):

    def __init__(self):
        self.service = UserService()

    @method_decorator(require_http_methods(['POST']))
    def post(self, request):
        response = {
            "code": "",
            "message": "",
            "data": {}
        }
        try:
            request_data = json.loads(request.body)
            username = request_data.get('username')
            password = request_data.get('password')
            service_response = self.service.user_login(request, username, password)

            response["code"] = service_response["code"]
            response["message"] = service_response["message"]
            response["data"] = service_response["data"]
            return JsonResponse(status=service_response["status_code"], data=response)

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)




