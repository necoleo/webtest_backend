from datetime import datetime

from django.core.paginator import Paginator
from django.db import transaction
from django.utils.decorators import method_decorator

from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_params_blank
from projects.models import ProjectModel
from utils.cos.cos_client import CosClient


class Service:

    def __init__(self):
        # 本地缓存目录
        self.COS_FILE_SAVED_TEMP = "cos_file_temp"
        self.cos_client = CosClient()

    @method_decorator(valid_params_blank(required_params_list=["page", "page_size"]))
    def get_project_list(self, page, page_size, project_id=None, project_name=None, project_type=None, project_status=None, start_date=None, end_date=None  ):
        """
        获取项目列表
        :param page: 页码（必填）
        :param page_size: 分页大小（必填）
        :param project_id: 项目id
        :param project_name: 项目名称
        :param project_type: 项目类型
        :param project_status: 项目状态
        :param start_date: 计划开始日期
        :param end_date: 计划结束日期
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        #  参数校验
        if not isinstance(page, int) or not isinstance(page_size, int):
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "参数无效"
            response['status_code'] = 400
            return response
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100

        try:
            filter_map = {
                "deleted_at__isnull": True
            }

            if project_id:
                # 精准查询
                filter_map["id"] = project_id

            if project_name:
                # 模糊查询
                filter_map["project_name__contains"] = project_name

            if project_type:
                # 模糊查询
                filter_map["project_type__contains"] = project_type

            if project_status:
                # 精准查询
                filter_map["project_status"] = project_status

            if start_date:
                filter_map["start_date__gte"] = start_date

            if end_date:
                filter_map["end_date__lte"] = end_date

            query_set = ProjectModel.objects.filter(**filter_map)

            paginator = Paginator(query_set, page_size)
            page_obj = paginator.get_page(page)

            query_results = page_obj.object_list
            results = []
            for project_obj in query_results:
                project_info = {
                    "id": project_obj.id,
                    "project_name": project_obj.project_name,
                    "project_type": project_obj.project_type,
                    "project_status": project_obj.project_status,
                    "start_date": project_obj.start_date,
                    "end_date": project_obj.end_date,
                    "description": project_obj.description,
                    "created_user_id": project_obj.created_user_id,
                    "created_user": project_obj.created_user,
                    "created_at": project_obj.created_at,
                    "updated_at": project_obj.updated_at
                }
                if project_info["start_date"]:
                    project_info["start_date"] = project_info["start_date"].strftime("%Y-%m-%d")
                if project_info["end_date"]:
                    project_info["end_date"] = project_info["end_date"].strftime("%Y-%m-%d")
                if project_info["created_at"]:
                    project_info["created_at"] = project_info["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                if project_info["updated_at"]:
                    project_info["updated_at"] = project_info["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

                results.append(project_info)

            current_page = page_obj.number
            total_count = paginator.count
            total_pages = paginator.num_pages

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询项目列表成功"
            response["data"]["results"] = results
            response['data']['total_count'] = total_count
            response['data']['total_pages'] = total_pages
            response['data']['current_page'] = current_page
            response['data']['page_size'] = page_size

            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500

            return response


    def create_project(self, project_param_dict):
        """
        创建项目
        :param project_param_dict: 项目参数字段
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        if not project_param_dict:
            response['code'] = ErrorCode.PARAM_BLANK
            response['message'] = '参数为空'
            response['status_code'] = 400
            return response

        try:
            project_name = project_param_dict.get("project_name")

            # 检查项目名称是否已存在
            if ProjectModel.objects.filter(project_name=project_name, deleted_at__isnull=True).exists():
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "项目名称已存在"
                response["status_code"] = 400
                return response

            # 创建项目
            project = ProjectModel.objects.create(
                project_name=project_name,
                description=project_param_dict.get("description"),
                project_type=project_param_dict.get("project_type"),
                project_status=project_param_dict.get("project_status", 0),
                start_date=project_param_dict.get("start_date"),
                end_date=project_param_dict.get("end_date"),
                created_user_id=project_param_dict.get("created_user_id"),
                created_user=project_param_dict.get("created_user")
            )

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "创建成功"
            response["data"]["project_id"] = project.id
            response["data"]["project_name"] = project.project_name

            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    def update_project(self, project_param_dict: dict):
        """
        更新项目
        :param project_param_dict: {
            "project_id": int (必填),
            "project_name": str,
            "description": str,
            "project_type": str,
            "project_status": int,
            "start_date": date,
            "end_date": date
        }
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        if not project_param_dict:
            response['code'] = ErrorCode.PARAM_BLANK
            response['message'] = '参数为空'
            response['status_code'] = 400
            return response

        try:
            project_id = project_param_dict.get("project_id")

            # 查询项目是否存在
            try:
                project = ProjectModel.objects.get(id=project_id, deleted_at__isnull=True)
            except ProjectModel.DoesNotExist:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "该项目不存在"
                response["status_code"] = 400
                return response

            # 如果修改了项目名称，检查是否重复
            new_project_name = project_param_dict.get("project_name")
            if new_project_name and new_project_name != project.project_name:
                if ProjectModel.objects.filter(project_name=new_project_name, deleted_at__isnull=True).exists():
                    response["code"] = ErrorCode.PARAM_INVALID
                    response["message"] = "项目名称已存在"
                    response["status_code"] = 400
                    return response
                project.project_name = new_project_name

            # 更新字段（只更新传入的字段）
            if "description" in project_param_dict:
                project.description = project_param_dict.get("description")
            if "project_type" in project_param_dict:
                project.project_type = project_param_dict.get("project_type")
            if "project_status" in project_param_dict:
                project.project_status = project_param_dict.get("project_status")
            if "start_date" in project_param_dict:
                project.start_date = project_param_dict.get("start_date")
            if "end_date" in project_param_dict:
                project.end_date = project_param_dict.get("end_date")

            project.save()

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "更新成功"
            response["data"]["project_id"] = project.id
            response["data"]["project_name"] = project.project_name

            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response


    @method_decorator(valid_params_blank(required_params_list=["project_id"]))
    def delete_project(self, project_id):
        """
        删除项目
        :param project_id:
        :return:
        """

        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        # 校验参数
        if not isinstance(project_id, int):
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "参数无效"
            response['status_code'] = 400
            return response

        try:
            with transaction.atomic():
                # 删除接口文档
                target_project = ProjectModel.objects.get(id=project_id, deleted_at__isnull=True)
                target_project.deleted_at = datetime.now()
                target_project.save()

                response["code"] = ErrorCode.SUCCESS
                response["message"] = "删除成功"
                response['data']['api_document_id'] = project_id
                return response

        except ProjectModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "该项目不存在"
            response['status_code'] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response['status_code'] = 500
            return response
