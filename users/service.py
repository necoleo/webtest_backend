from django.contrib.auth import authenticate, login

from users import models as users_model


class UserService:


    def user_login(self, request, username, password):
        """用户登录"""
        response = {}

        try:
            # 验证用户名和密码是否正确
            user_obj = authenticate(username=username, password=password)
        except Exception as e:
            response['code'] = "error"
            response['message'] = "登录过程中发生错误"
            response['data'] = str(e)
            return response

        if user_obj is None:
            response['code'] = "error"
            response['message'] = "账号密码错误"
            response['data'] = ""
            return response
        else:
            try:
                login(request, user_obj)
                response['code'] = "success"
                response['message'] = "登录成功"
                response['data'] = f"用户 {user_obj.get_username()} 登录成功"
            except Exception as e:
                response['code'] = "error"
                response['message'] = "登录失败"
                response['data'] = str(e)
                return response
        return response



