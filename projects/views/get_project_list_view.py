from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required
from projects.service import Service


class GetProjectListView(View):
    """
    获取项目列表接口
    """
    def __init__(self):
        self.service = Service()


    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(["GET"]))
    def get(self, request):
        """
        获取接口文档列表接口
        :param request:
        :return:
        """

        response = {
        "code": "",
        "message": "",
        "data": {}
        }

        try:
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 20))
            project_id = request.GET.get("id")
            if project_id:
                project_id = int(project_id)
            project_name = request.GET.get("project_name")
            project_type = request.GET.get("project_type")
            project_status = request.GET.get("project_status")
            if project_status:
                project_status = int(project_status)
            start_date = request.GET.get("start_date")
            end_date = request.GET.get("end_date")


            service_response = self.service.get_project_list(page, page_size, project_id, project_name, project_type, project_status,start_date,end_date)
            response['code'] = service_response['code']
            response['message'] = service_response['message']
            response['data'] = service_response['data']

            return JsonResponse(status=service_response['status_code'], data=response)

        except  (ValueError, TypeError) as e:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = str(e)
            response['status_code'] = 400
            return response

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = str(e)
            return JsonResponse(status=500, data=response)