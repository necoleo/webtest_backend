import os

from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from qcloud_cos import CosClientError

from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_params_blank
from requirements.models import RequirementDocumentModel
from utils.cos.cos_client import CosClient


class Service:

    def __init__(self):
        # 本地缓存目录
        self.COS_FILE_SAVED_TEMP = "cos_file_temp"
        self.cos_client = CosClient()

    @method_decorator(valid_params_blank(required_params_list=["project_id", "version", "file", "comment", "created_user_id", "created_user"]))
    def upload_requirement_document(self, project_id, version, file, comment, created_user_id, created_user):
        """
        上传需求文档
        :param project_id: 所属项目id
        :param version: 需求文档版本号
        :param file: 需求文档文件
        :param comment: 备注
        :param created_user_id: 创建人id
        :param created_user: 创建人
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        try:
            # 将文件缓存至本地
            upload_file = FileSystemStorage(location=self.COS_FILE_SAVED_TEMP)
            saved_filename = upload_file.save(file.name, file)
            if not saved_filename:
                response["code"] = ErrorCode.FILE_SAVE_FAILED
                response["message"] = "文件保存失败"
                response["status_code"] = 500
                return response

            # 设置 COS 目标目录（按项目分目录）
            target_dir = f"webtest_requirement_document/{project_id}/"
            temp_dir = os.path.abspath(self.COS_FILE_SAVED_TEMP)
            temp_file_path = os.path.join(temp_dir, saved_filename)
            # 上传需求文档到 COS
            cos_res = self.cos_client.upload_file_to_cos_bucket(target_dir, saved_filename, temp_file_path)

            # 判断上传是否成功（SDK 通常返回包含 ETag 的响应头）
            if not cos_res or 'ETag' not in cos_res:
                response['code'] = ErrorCode.FILE_SAVE_FAILED
                response['message'] = f"上传失败: {cos_res}"
                response['status_code'] = 500
                return response

            # 生成 COS 对象键与访问链接
            cos_key = f"{target_dir}{file.name}"
            cos_access_url = f"https://{self.cos_client.bucket}.cos.ap-guangzhou.myqcloud.com/{cos_key}"
            # 计算文件大小
            file_size = os.path.getsize(temp_file_path)
            # 删除缓存文件
            upload_file.delete(saved_filename)

            # 创建需求文档记录
            requirement_document = RequirementDocumentModel.objects.create(
                project_id=project_id,
                doc_name=file.name,
                version=version,
                cos_access_url=cos_access_url,
                file_size=file_size,
                comment=comment,
                created_user_id=created_user_id,
                created_user=created_user
            )

            response['code'] = ErrorCode.SUCCESS
            response['message'] = "上传成功"
            response['data']['document_id'] = requirement_document.id
            response['data']['project_id'] = project_id
            response['data']['cos_access_url'] = cos_access_url
            response['data']['file_size'] = file_size
            response['data']['etag'] = cos_res['ETag']
            response['status_code'] = 200

            return response

        except CosClientError as e:
            response['code'] = ErrorCode.FILE_SAVE_FAILED
            response['message'] = f"上传过程中发生错误：COS 客户端异常：{str(e)}"
            response['status_code'] = 500

            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500

            return response

    @method_decorator(valid_params_blank(required_params_list=["page", "page_size"]))
    def get_requirement_document(self, page, page_size, requirement_document_id=None, project_id=None, doc_name=None, version=None):
        """
       获取需求文档
       :param page: 页码（必填）
       :param page_size: 分页大小（必填）
       :param requirement_document_id: 需求文档id
       :param project_id: 所属项目id
       :param doc_name: 需求文档名称
       :param version: 需求文档版本
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

            if requirement_document_id is not None:
                # 精准查询
                filter_map["id"] = requirement_document_id

            if project_id is not None:
                # 精准查询
                filter_map["project_id"] = project_id

            if doc_name:
                # 模糊查询
                filter_map["doc_name__contains"] = doc_name

            if version is not None:
                # 模糊查询
                filter_map["version__contains"] = version

            query_set = RequirementDocumentModel.objects.filter(**filter_map)

            paginator = Paginator(query_set, page_size)
            page_obj = paginator.get_page(page)

            query_results = page_obj.object_list
            results = []
            for requirement_document_obj in query_results:
                requirement_document_info = {
                    "id": requirement_document_obj.id,
                    "project_id": requirement_document_obj.project_id,
                    "doc_name": requirement_document_obj.doc_name,
                    "version": requirement_document_obj.version,
                    "cos_access_url": requirement_document_obj.cos_access_url,
                    "file_size": requirement_document_obj.file_size,
                    "comment": requirement_document_obj.comment,
                    "parse_status": requirement_document_obj.parse_status,
                    "created_user_id": requirement_document_obj.created_user_id,
                    "requirement_count": requirement_document_obj.requirement_count,
                    "created_user": requirement_document_obj.created_user,
                    "created_at": requirement_document_obj.created_at,
                    "updated_at": requirement_document_obj.updated_at
                }
                if requirement_document_info["created_at"]:
                    requirement_document_info["created_at"] = requirement_document_info["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                if requirement_document_info["updated_at"]:
                    requirement_document_info["updated_at"] = requirement_document_info["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

                results.append(requirement_document_info)

            current_page = page_obj.number
            total_count = paginator.count
            total_pages = paginator.num_pages

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询需求文档成功"
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

    @method_decorator(valid_params_blank(required_params_list=["requirement_document_id"]))
    def update_requirement_document(self, requirement_document_id, doc_name=None, version=None, comment=None):
        """
        编辑需求文档
        :param requirement_document_id: 需求文档id，必填
        :param doc_name: 需求文档名称，可选
        :param version: 需求文档版本，可选
        :param comment: 需求文档备注，可选
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        if not doc_name and not version and not comment:
            response["code"] = ErrorCode.PARAM_BLANK
            response["message"] = "参数为空"
            response['status_code'] = 400
            return response

        try:
            requirement_document = RequirementDocumentModel.objects.get(id=requirement_document_id, deleted_at__isnull=True)

            if not requirement_document:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "该文档不存在"
                response['status_code'] = 400
                return response

            if doc_name:
                requirement_document.doc_name = doc_name
            if version:
                requirement_document.version = version
            if comment:
                requirement_document.comment = comment

            requirement_document.save(update_fields=["doc_name", "version", "comment"])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "更新成功"
            response["data"] = {
                "requirement_document_id": requirement_document.id,
                "doc_name": requirement_document.doc_name,
                "version": requirement_document.version,
                "comment": requirement_document.comment
            }
            return response

        except Exception as e:
            response["message"] = f"错误信息: {str(e)}"
            response['status_code'] = 500
            return response