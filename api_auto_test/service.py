import os
from datetime import datetime

import requests
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db import transaction
from django.utils.decorators import method_decorator

from api_auto_test.models import ApiDocuments, ApiInterfaceModel
from api_auto_test.parser.api_document_parser import ApiDocumentParser
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_params_blank
from utils.cos.cos_client import CosClient
from qcloud_cos import CosClientError



class Service:
    def __init__(self):
        # 本地缓存目录
        self.COS_FILE_SAVED_TEMP = "cos_file_temp"
        self.cos_client = CosClient()

    @method_decorator(valid_params_blank(required_params_list=["project_id", "version", "file", "comment", "created_user"]))
    def upload_api_document(self, project_id, version, file, comment, created_user):
        """
        上传接口文档
        :param project_id: 所属项目id
        :param version: 接口文档版本号
        :param file: 接口文档文件
        :param comment: 备注
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
            target_dir = f"webtest_api_document/{project_id}/"
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

            # 创建接口文档记录
            api_document = ApiDocuments.objects.create(
                project_id=project_id,
                doc_name=file.name,
                version=version,
                cos_access_url=cos_access_url,
                file_size=file_size,
                comment=comment,
                created_user=created_user
            )

            response['code'] = ErrorCode.SUCCESS
            response['message'] = "上传成功"
            response['data']['document_id'] = api_document.id
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
    def get_api_document(self, page, page_size, api_document_id=None, project_id=None, doc_name=None, version=None):
        """
        获取接口文档
        :param page: 页码（必填）
        :param page_size: 分页大小（必填）
        :param api_document_id: 接口文档id
        :param project_id: 所属项目id
        :param doc_name: 接口文档名称
        :param version: 接口文档版本
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

            if api_document_id:
                # 精准查询
                filter_map["id"] = api_document_id

            if project_id:
                # 精准查询
                filter_map["project_id"] = project_id

            if doc_name:
                # 模糊查询
                filter_map["doc_name__contains"] = doc_name

            if version:
                # 模糊查询
                filter_map["version__contains"] = version

            query_set = ApiDocuments.objects.filter(**filter_map)

            paginator = Paginator(query_set, page_size)
            page_obj = paginator.get_page(page)

            query_results = page_obj.object_list
            results = []
            for api_document_obj in query_results:
                api_document_info = {
                    "id": api_document_obj.id,
                    "project_id": api_document_obj.project_id,
                    "doc_name": api_document_obj.doc_name,
                    "version": api_document_obj.version,
                    "cos_access_url": api_document_obj.cos_access_url,
                    "file_size": api_document_obj.file_size,
                    "comment": api_document_obj.comment,
                    "is_parsed": api_document_obj.is_parsed,
                    "created_user": api_document_obj.created_user,
                    "created_at": api_document_obj.created_at,
                    "updated_at": api_document_obj.updated_at
                }
                if api_document_info["created_at"]:
                    api_document_info["created_at"] = api_document_info["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                if api_document_info["updated_at"]:
                    api_document_info["updated_at"] = api_document_info["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

                results.append(api_document_info)


            current_page = page_obj.number
            total_count = paginator.count
            total_pages = paginator.num_pages

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询接口文档成功"
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


    @method_decorator(valid_params_blank(required_params_list=["api_document_id"]))
    def delete_api_document(self, api_document_id):
        """
        删除接口文档
        :param api_document_id:
        :return:
        """

        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        # 校验参数
        if not isinstance(api_document_id, int):
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "参数无效"
            response['status_code'] = 400
            return response

        try:
            with transaction.atomic():
                # 删除接口文档
                target_api_document = ApiDocuments.objects.get(id=api_document_id, deleted_at__isnull=True)
                target_api_document.deleted_at = datetime.now()
                target_api_document.save()
                # 删除所有关联的接口
                ApiInterfaceModel.objects.filter(
                    document_id=api_document_id,
                    deleted_at__isnull=True
                ).update(deleted_at=datetime.now())

                response["code"] = ErrorCode.SUCCESS
                response["message"] = "删除成功"
                response['data']['api_document_id'] = api_document_id
                return response

        except ApiDocuments.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "该接口文档不存在"
            response['status_code'] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response['status_code'] = 500
            return response


    @method_decorator(valid_params_blank(required_params_list=["api_document_id"]))
    def parse_api_document(self, api_document_id):
        """
        将接口文档解析成接口列表并保存到数据库
        :param api_document_id: 接口文档的id
        :param file_content: 接口文档的内容
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:

            # 获取接口文档
            api_document = ApiDocuments.objects.get(id=api_document_id, deleted_at__isnull=True)

            # 判断是否已解析
            if api_document.is_parsed:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "该文档已解析"
                response["status_code"] = 400
                return response

            # 下载接口文档内容
            file_content = self.cos_client.download_and_read_json_by_url(api_document.cos_access_url, self.COS_FILE_SAVED_TEMP )

            if not file_content:
                response["code"] = ErrorCode.SERVER_ERROR
                response["message"] = "获取文件失败"
                response['status_code'] = 500
                return response

            # 解析文档
            parser = ApiDocumentParser(api_document_id, file_content)

            api_document_type = parser.check_api_document_type()

            if api_document_type == "swagger":
                api_interface_list = parser.parser_swagger()

            else:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "不支持的文档格式"
                response['status_code'] = 400
                return response

            # 使用事务
            with transaction.atomic():
                # 批量保存到数据库
                api_interface_model_list = []
                for item in api_interface_list:
                    api_interface_model = ApiInterfaceModel(**item)
                    api_interface_model_list.append(api_interface_model)

                ApiInterfaceModel.objects.bulk_create(api_interface_model_list)

                api_document.is_parsed = True
                api_document.save(update_fields=["is_parsed"])

                response["code"] = ErrorCode.SUCCESS
                response["message"] = f"成功导入 {len(api_interface_list)} 个接口"
                response["data"]["count"] = len(api_interface_list)

            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"错误信息: {str(e)}"
            response['status_code'] = 500
            return response


    @method_decorator(valid_params_blank(required_params_list=["api_document_id"]))
    def update_api_document(self, api_document_id, doc_name=None, version=None, comment=None):
        """
        编辑接口文档
        :param api_document_id: 接口文档id，必填
        :param doc_name: 接口文档名称，可选
        :param version: 接口文档版本，可选
        :param comment: 接口文档备注，可选
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
            api_document = ApiDocuments.objects.get(id=api_document_id, deleted_at__isnull=True)

            if not api_document:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "该文档不存在"
                response['status_code'] = 400
                return response

            if doc_name:
                api_document.doc_name = doc_name
            if version:
                api_document.version = version
            if comment:
                api_document.comment = comment

            api_document.save(update_fields=["doc_name", "version", "comment"])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "更新成功"
            response["data"] = {
                "api_document_id": api_document.id,
                "doc_name": api_document.doc_name,
                "version": api_document.version,
                "comment": api_document.comment
            }
            return response

        except Exception as e:
            response["message"] = f"错误信息: {str(e)}"
            response['status_code'] = 500
            return response

