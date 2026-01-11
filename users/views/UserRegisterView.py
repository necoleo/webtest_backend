import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from users.service import UserService


class UserRegisterView(View):

    service = UserService()

    @method_decorator(require_http_methods(['POST']))
    def post(self, request):

        request_data = json.loads(request.body)
        username = request_data.get('username')
        password = request_data.get('password')
        check_password = request_data.get('check_password')

        response = self.service.user_register(username, password, check_password)

        return JsonResponse(status=200, data=response)
