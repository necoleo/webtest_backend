import json
import re

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from users.service import UserService


# Create your views here.
class UserLoginView(View):

    service = UserService()

    @method_decorator(require_http_methods(['POST']))
    def post(self, request):

        request_data = json.loads(request.body)
        username = request_data.get('username')
        password = request_data.get('password')

        response = self.service.user_login(request, username, password)

        return JsonResponse(status=200, data=response)



