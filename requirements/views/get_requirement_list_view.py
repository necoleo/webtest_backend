from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required
from requirements.service import Service


class GetRequirementListView(View):

    def __init__(self):
        self.service = Service()


    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(["GET"]))
    def get(self, request):
        """
        获取需求项列表接口
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
            requirement_id = request.GET.get("requirement_id")
            if requirement_id:
                requirement_id = int(requirement_id)
            project_id = request.GET.get("project_id")
            if project_id:
                project_id = int(project_id)
            requirement_document_id = request.GET.get("requirement_document_id")
            if requirement_document_id:
                requirement_document_id = int(requirement_document_id)
            requirement_title = request.GET.get("requirement_title")
            requirement_content = request.GET.get("requirement_content")
            module = request.GET.get("module")
            status = request.GET.get("status")
            if status:
                status = int(status)
            is_vectorized = request.GET.get("is_vectorized")
            if is_vectorized:
                is_vectorized = int(is_vectorized)

            service_response = self.service.get_requirement(page,page_size,requirement_id, project_id, requirement_document_id,
                        requirement_title, requirement_content, module, status, is_vectorized)
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