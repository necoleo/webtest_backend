from django.http import JsonResponse


def valid_login_required(func):
    """登录状态装饰器"""
    def wrapper(request, *args, **kwargs):
        response = {}
        if not request.user.is_authenticated:
            response['code'] = "error"
            response['message'] = "未授权"
            response['data'] = ""
            return JsonResponse(status=401, data=response)
        result = func(request, *args, **kwargs)
        return result
    return wrapper
