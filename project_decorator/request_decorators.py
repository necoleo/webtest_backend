import inspect
import json
from functools import wraps

from django.http import JsonResponse

from constant.error_code import ErrorCode


def valid_login_required(func):
    """登录状态装饰器"""
    def wrapper(request, *args, **kwargs):
        response = {}
        if not request.user.is_authenticated:
            response['code'] = ErrorCode.UNAUTHORIZED
            response['message'] = "未授权"
            response['data'] = ""
            return JsonResponse(status=401, data=response)
        result = func(request, *args, **kwargs)
        return result
    return wrapper

def valid_params_blank(required_params_list):
    """
    校验入参是否为 blank
    :param required_params_list: 入参列表
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = {
                "code": "",
                "message": "",
                "data": {}
            }

            # 获取参数
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            # 构建参数字典：位置参数 + 关键字参数
            params = {}
            if param_names and param_names[0] in ["self", "cls"]:
                param_names = param_names[1:]

            count = 0
            for param in param_names:
                if param in required_params_list:
                    params[param] = args[count]
                count += 1
            # 关键字参数覆盖位置参数
            params.update(kwargs)

            # 校验每个参数是否为blank
            blank_params_list = []
            for param in required_params_list:
                value = params.get(param)
                #  参数缺失
                if value is None:
                    blank_params_list.append(param)
                    continue
                # 判断字符串是否为空
                if isinstance(value, str):
                    if not value.strip():
                        blank_params_list.append(param)
                    continue
                # 判断列表/字典是否为空
                if isinstance(value, (list, dict)):
                    if not value:
                        blank_params_list.append(param)
                    continue

                #  解析JSON字符串
                try:
                    json_param = json.loads(value)
                    if not json_param or json_param is None:
                        blank_params_list.append(param)
                except:
                    pass

            if blank_params_list:
                response['code'] = ErrorCode.PARAM_BLANK
                response['message'] = f"参数为空: {','.join(blank_params_list)}"
                return response
            return func(*args, **kwargs)
        return wrapper
    return decorator
