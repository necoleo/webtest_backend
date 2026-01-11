from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from django.utils.decorators import method_decorator

from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_params_blank
from users import models as users_model


class UserService:

    @method_decorator(valid_params_blank(required_params_list=["username", "password"]))
    def user_login(self, request, username, password):
        """用户登录"""
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            # 验证用户名和密码是否正确
            user_obj = authenticate(username=username, password=password)
        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = "登录过程中发生错误"
            response['data'] = str(e)
            return response

        if user_obj is None:
            response['code'] = ErrorCode.LOGIN_FAILED
            response['message'] = "账号密码错误"
            response['data'] = ""
            return response
        else:
            try:
                login(request, user_obj)
                response['code'] = ErrorCode.SUCCESS
                response['message'] = "登录成功"
                response['data'] = f"用户 {user_obj.get_username()} 登录成功"
            except Exception as e:
                response['code'] = ErrorCode.SERVER_ERROR
                response['message'] = "登录失败"
                response['data'] = str(e)
                return response
        return response


    def user_register(self, username, password, check_password):
        """用户注册"""
        response = {}
        if check_password != password:
            response['code'] = "error"
            response['message'] = "两次输入的密码不一致"
            response['data'] = ""
            return response
        try:
            user_obj = users_model.User.objects.create_user(username=username, password=password)
            response['code'] = "success"
            response['message'] = "注册成功"
            response['data'] = f"{user_obj.get_username()} 注册成功"

        except IntegrityError as e:
            response['code'] = "error"
            response['message'] = "账号存在"
            response['data'] = str(e)
            return response

        except Exception as e:
            response['code'] = "error"
            response['message'] = "注册过程发生错误"
            response['data'] = str(e)
            return response
        return response