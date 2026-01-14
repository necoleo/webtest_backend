from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods

from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_login_required
from requirements.serivce import Service


class GetRequirementDocumentListView(View):

    def __init__(self):
        self.service = Service()


    @method_decorator(valid_login_required)
    @method_decorator(require_http_methods(["GET"]))
    def get(self, request):
        """
        获取需求文档列表接口
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
            requirement_document_id = request.GET.get("id")
            if requirement_document_id:
                requirement_document_id = int(requirement_document_id)
            project_id = request.GET.get("project_id")
            if project_id:
                project_id = int(project_id)
            doc_name = request.GET.get("doc_name")
            version = request.GET.get("version")

            service_response = self.service.get_requirement_document(page, page_size, requirement_document_id, project_id, doc_name, version)
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