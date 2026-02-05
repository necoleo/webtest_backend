import os
from datetime import datetime, timedelta

import yaml
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from qcloud_cos import CosClientError

from api_auto_test.models import (
    ApiDocumentsModel,
    ApiInterfaceModel,
    ApiTestCaseModel,
    ApiTestEnvironmentModel,
    ApiTestExecutionModel,
    ApiTestScheduleModel
)
from api_auto_test.parser.api_document_parser import ApiDocumentParser
from constant.error_code import ErrorCode
from project_decorator.request_decorators import valid_params_blank
from tasks.api_test_tasks import ApiTestTaskService
from utils.cos.cos_client import CosClient



class Service:
    def __init__(self):
        # 本地缓存目录
        self.COS_FILE_SAVED_TEMP = "cos_file_temp"
        self.cos_client = CosClient()

    @valid_params_blank(required_params_list=["project_id", "version", "file", "comment", "created_user_id", "created_user"])
    def upload_api_document(self, project_id, version, file, comment, created_user_id, created_user):
        """
        上传接口文档
        :param project_id: 所属项目id
        :param version: 接口文档版本号
        :param file: 接口文档文件
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
            target_dir = f"webtest/webtest_api_document/{project_id}/"
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
            api_document = ApiDocumentsModel.objects.create(
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

    @valid_params_blank(required_params_list=["api_document_id"])
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
            api_document = ApiDocumentsModel.objects.get(id=api_document_id, deleted_at__isnull=True)

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

    @valid_params_blank(required_params_list=["page", "page_size"])
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

            query_set = ApiDocumentsModel.objects.filter(**filter_map)

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
                    "created_user_id": api_document_obj.created_user_id,
                    "created_user": api_document_obj.created_user,
                    "created_at": api_document_obj.created_at,
                    "updated_at": api_document_obj.updated_at
                }
                if api_document_info["created_at"]:
                    api_document_info["created_at"] = timezone.localtime(api_document_info["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
                if api_document_info["updated_at"]:
                    api_document_info["updated_at"] = timezone.localtime(api_document_info["updated_at"]).strftime("%Y-%m-%d %H:%M:%S")

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


    @valid_params_blank(required_params_list=["api_document_id"])
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
                target_api_document = ApiDocumentsModel.objects.get(id=api_document_id, deleted_at__isnull=True)
                target_api_document.deleted_at = timezone.now()
                target_api_document.save()
                # 删除所有关联的接口
                ApiInterfaceModel.objects.filter(
                    document_id=api_document_id,
                    deleted_at__isnull=True
                ).update(deleted_at=timezone.now())

                response["code"] = ErrorCode.SUCCESS
                response["message"] = "删除成功"
                response['data']['api_document_id'] = api_document_id
                return response

        except ApiDocumentsModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "该接口文档不存在"
            response['status_code'] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response['status_code'] = 500
            return response

    @valid_params_blank(required_params_list=["api_document_id"])
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
            api_document = ApiDocumentsModel.objects.get(id=api_document_id, deleted_at__isnull=True)

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

    # ==================== 接口测试用例管理 ====================

    @valid_params_blank(required_params_list=["project_id", "module", "case_name", "file", "created_user_id", "created_user"])
    def upload_api_test_case(self, project_id, module, case_name, file, created_user_id, created_user, description=None):
        """
        上传接口测试用例
        :param project_id: 所属项目id
        :param module: 所属模块
        :param case_name: 用例名称
        :param file: YAML文件
        :param created_user_id: 创建人id
        :param created_user: 创建人
        :param description: 用例描述
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        # 校验文件类型
        if not file.name.endswith(('.yaml', '.yml')):
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "文件类型错误，仅支持 .yaml 或 .yml 文件"
            response["status_code"] = 400
            return response

        # 临时文件相关变量
        upload_file = None
        saved_filename = None

        try:
            # 将文件缓存至本地
            upload_file = FileSystemStorage(location=self.COS_FILE_SAVED_TEMP)
            saved_filename = upload_file.save(file.name, file)
            if not saved_filename:
                response["code"] = ErrorCode.FILE_SAVE_FAILED
                response["message"] = "文件保存失败"
                response["status_code"] = 500
                return response

            temp_dir = os.path.abspath(self.COS_FILE_SAVED_TEMP)
            temp_file_path = os.path.join(temp_dir, saved_filename)

            # 校验 YAML 格式
            try:
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    yaml_content = yaml.safe_load(f)
                if not yaml_content or 'config' not in yaml_content or 'cases' not in yaml_content:
                    response["code"] = ErrorCode.PARAM_INVALID
                    response["message"] = "YAML 格式错误，必须包含 config 和 cases 字段"
                    response["status_code"] = 400
                    return response
            except yaml.YAMLError as e:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = f"YAML 解析失败: {str(e)}"
                response["status_code"] = 400
                return response

            # 设置 COS 目标目录（按项目分目录）
            target_dir = f"webtest/webtest_api_test_cases/{project_id}/"

            # 上传到 COS
            cos_res = self.cos_client.upload_file_to_cos_bucket(target_dir, saved_filename, temp_file_path)

            # 判断上传是否成功
            if not cos_res or 'ETag' not in cos_res:
                response['code'] = ErrorCode.FILE_SAVE_FAILED
                response['message'] = f"上传失败: {cos_res}"
                response['status_code'] = 500
                return response

            # 生成 COS 访问链接
            cos_key = f"{target_dir}{saved_filename}"
            cos_access_url = f"https://{self.cos_client.bucket}.cos.ap-guangzhou.myqcloud.com/{cos_key}"
            # 计算文件大小
            file_size = os.path.getsize(temp_file_path)

            # 创建测试用例记录
            test_case = ApiTestCaseModel.objects.create(
                project_id=project_id,
                module=module,
                case_name=case_name,
                description=description,
                cos_access_url=cos_access_url,
                file_size=file_size,
                source=ApiTestCaseModel.CaseSource.UPLOAD,
                created_user_id=created_user_id,
                created_user=created_user
            )

            response['code'] = ErrorCode.SUCCESS
            response['message'] = "上传成功"
            response['data'] = {
                'test_case_id': test_case.id,
                'project_id': project_id,
                'case_name': case_name,
                'cos_access_url': cos_access_url,
                'file_size': file_size
            }

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

        finally:
            # 确保临时文件被清理
            if upload_file and saved_filename:
                try:
                    upload_file.delete(saved_filename)
                except Exception:
                    pass

    @valid_params_blank(required_params_list=["page", "page_size"])
    def get_api_test_case_list(self, page, page_size, project_id=None, case_name=None, source=None, module=None):
        """
        获取接口测试用例列表
        :param page: 页码
        :param page_size: 分页大小
        :param project_id: 所属项目id
        :param case_name: 用例名称（模糊查询）
        :param source: 用例来源
        :param module: 所属模块
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        # 参数校验
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
                filter_map["project_id"] = project_id

            if case_name:
                filter_map["case_name__contains"] = case_name

            if source is not None:
                filter_map["source"] = source

            if module:
                filter_map["module"] = module

            query_set = ApiTestCaseModel.objects.filter(**filter_map).order_by('-created_at')

            paginator = Paginator(query_set, page_size)
            page_obj = paginator.get_page(page)

            results = []
            for obj in page_obj.object_list:
                item = {
                    "id": obj.id,
                    "project_id": obj.project_id,
                    "module": obj.module,
                    "case_name": obj.case_name,
                    "description": obj.description,
                    "cos_access_url": obj.cos_access_url,
                    "file_size": obj.file_size,
                    "source": obj.source,
                    "source_label": obj.get_source_display(),
                    "last_execution_status": obj.last_execution_status,
                    "last_execution_status_label": obj.get_last_execution_status_display() if obj.last_execution_status is not None else None,
                    "last_execution_time": timezone.localtime(obj.last_execution_time).strftime("%Y-%m-%d %H:%M:%S") if obj.last_execution_time else None,
                    "total_executions": obj.total_executions,
                    "success_count": obj.success_count,
                    "created_user_id": obj.created_user_id,
                    "created_user": obj.created_user,
                    "created_at": timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else None,
                    "updated_at": timezone.localtime(obj.updated_at).strftime("%Y-%m-%d %H:%M:%S") if obj.updated_at else None
                }
                results.append(item)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询成功"
            response["data"] = {
                "results": results,
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "page_size": page_size
            }

            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["test_case_id"])
    def get_api_test_case_yaml_content(self, test_case_id):
        """
        获取接口测试用例的 YAML 内容
        :param test_case_id: 测试用例id
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            test_case = ApiTestCaseModel.objects.get(id=test_case_id, deleted_at__isnull=True)

            if not test_case.cos_access_url:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "该测试用例没有关联的 YAML 文件"
                response["status_code"] = 400
                return response

            # 通过 COS 客户端下载并读取 YAML 内容
            yaml_content = self.cos_client.download_and_read_text_by_url(
                test_case.cos_access_url,
                self.COS_FILE_SAVED_TEMP
            )

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "获取成功"
            response["data"] = {
                "test_case_id": test_case.id,
                "case_name": test_case.case_name,
                "yaml_content": yaml_content
            }

            return response

        except ApiTestCaseModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "测试用例不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"获取 YAML 内容失败：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["test_case_id"])
    def get_api_test_case_detail(self, test_case_id):
        """
        获取接口测试用例详情
        :param test_case_id: 测试用例id
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            test_case = ApiTestCaseModel.objects.get(id=test_case_id, deleted_at__isnull=True)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询成功"
            response["data"] = {
                "id": test_case.id,
                "project_id": test_case.project_id,
                "case_name": test_case.case_name,
                "description": test_case.description,
                "cos_access_url": test_case.cos_access_url,
                "file_size": test_case.file_size,
                "source": test_case.source,
                "source_label": test_case.get_source_display(),
                "ai_source_interface_ids": test_case.ai_source_interface_ids,
                "last_execution_status": test_case.last_execution_status,
                "last_execution_status_label": test_case.get_last_execution_status_display() if test_case.last_execution_status is not None else None,
                "last_execution_time": timezone.localtime(test_case.last_execution_time).strftime("%Y-%m-%d %H:%M:%S") if test_case.last_execution_time else None,
                "total_executions": test_case.total_executions,
                "success_count": test_case.success_count,
                "created_user_id": test_case.created_user_id,
                "created_user": test_case.created_user,
                "created_at": timezone.localtime(test_case.created_at).strftime("%Y-%m-%d %H:%M:%S") if test_case.created_at else None,
                "updated_at": timezone.localtime(test_case.updated_at).strftime("%Y-%m-%d %H:%M:%S") if test_case.updated_at else None
            }

            return response

        except ApiTestCaseModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "测试用例不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    def get_api_test_case_module(self):
        """获取所有模块列表及数据"""
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        try:
            modules = ApiTestCaseModel.objects.filter(
                deleted_at__isnull=True,
                module__isnull=False
            ).values("module").annotate(
                count=Count("id")
            ).order_by("module")
            module_list = list(modules)
            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询接口测试用例模块成功"
            response["data"] = {
                "module": module_list,
            }
            return response
        except ApiTestCaseModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "不存在模块"
            response["status_code"] = 400
            return response
        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = str(e)
            response["status_code"] = 500
            return response


    @valid_params_blank(required_params_list=["test_case_id"])
    def delete_api_test_case(self, test_case_id):
        """
        删除接口测试用例（软删除），同时删除关联的定时任务
        :param test_case_id: 测试用例id
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            with transaction.atomic():
                test_case = ApiTestCaseModel.objects.get(id=test_case_id, deleted_at__isnull=True)

                # 软删除关联的定时任务
                deleted_schedules = ApiTestScheduleModel.objects.filter(
                    test_case_id=test_case_id,
                    deleted_at__isnull=True
                ).update(deleted_at=timezone.now())

                # 软删除测试用例
                test_case.deleted_at = timezone.now()
                test_case.save(update_fields=['deleted_at'])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "删除成功"
            response["data"] = {
                "test_case_id": test_case_id,
                "deleted_schedules": deleted_schedules
            }

            return response

        except ApiTestCaseModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "测试用例不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    # ==================== 接口测试环境配置管理 ====================

    @valid_params_blank(required_params_list=["project_id", "env_name", "base_url", "created_user_id", "created_user"])
    def create_api_test_environment(self, project_id, env_name, base_url, created_user_id, created_user,
                                     description=None, timeout=30, headers=None, variables=None, is_default=False):
        """
        创建接口测试环境配置
        :param project_id: 所属项目id
        :param env_name: 环境名称
        :param base_url: 基础URL
        :param created_user_id: 创建人id
        :param created_user: 创建人
        :param description: 环境描述
        :param timeout: 超时时间（秒）
        :param headers: 公共请求头
        :param variables: 环境变量
        :param is_default: 是否为默认环境
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            with transaction.atomic():
                # 如果设置为默认环境，先将该项目的其他环境设为非默认
                if is_default:
                    ApiTestEnvironmentModel.objects.filter(
                        project_id=project_id,
                        is_default=True,
                        deleted_at__isnull=True
                    ).update(is_default=False)

                environment = ApiTestEnvironmentModel.objects.create(
                    project_id=project_id,
                    env_name=env_name,
                    description=description,
                    base_url=base_url,
                    timeout=timeout,
                    headers=headers,
                    variables=variables,
                    is_default=is_default,
                    created_user_id=created_user_id,
                    created_user=created_user
                )

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "创建成功"
            response["data"] = {
                "environment_id": environment.id,
                "project_id": project_id,
                "env_name": env_name,
                "base_url": base_url
            }

            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["page", "page_size"])
    def get_api_test_environment_list(self, page, page_size, project_id=None, env_name=None):
        """
        获取接口测试环境配置列表
        :param page: 页码
        :param page_size: 分页大小
        :param project_id: 所属项目id
        :param env_name: 环境名称（模糊查询）
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        # 参数校验
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
                filter_map["project_id"] = project_id

            if env_name:
                filter_map["env_name__contains"] = env_name

            query_set = ApiTestEnvironmentModel.objects.filter(**filter_map).order_by('-is_default', '-created_at')

            paginator = Paginator(query_set, page_size)
            page_obj = paginator.get_page(page)

            results = []
            for obj in page_obj.object_list:
                item = {
                    "id": obj.id,
                    "project_id": obj.project_id,
                    "env_name": obj.env_name,
                    "description": obj.description,
                    "base_url": obj.base_url,
                    "timeout": obj.timeout,
                    "headers": obj.headers,
                    "variables": obj.variables,
                    "is_default": obj.is_default,
                    "created_user_id": obj.created_user_id,
                    "created_user": obj.created_user,
                    "created_at": timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else None,
                    "updated_at": timezone.localtime(obj.updated_at).strftime("%Y-%m-%d %H:%M:%S") if obj.updated_at else None
                }
                results.append(item)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询成功"
            response["data"] = {
                "results": results,
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "page_size": page_size
            }

            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["environment_id"])
    def update_api_test_environment(self, environment_id, env_name=None, description=None, base_url=None,
                                     timeout=None, headers=None, variables=None, is_default=None):
        """
        更新接口测试环境配置
        :param environment_id: 环境配置id
        :param env_name: 环境名称
        :param description: 环境描述
        :param base_url: 基础URL
        :param timeout: 超时时间
        :param headers: 公共请求头
        :param variables: 环境变量
        :param is_default: 是否为默认环境
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            with transaction.atomic():
                environment = ApiTestEnvironmentModel.objects.get(id=environment_id, deleted_at__isnull=True)

                update_fields = []

                if env_name is not None:
                    environment.env_name = env_name
                    update_fields.append('env_name')

                if description is not None:
                    environment.description = description
                    update_fields.append('description')

                if base_url is not None:
                    environment.base_url = base_url
                    update_fields.append('base_url')

                if timeout is not None:
                    environment.timeout = timeout
                    update_fields.append('timeout')

                if headers is not None:
                    environment.headers = headers
                    update_fields.append('headers')

                if variables is not None:
                    environment.variables = variables
                    update_fields.append('variables')

                if is_default is not None:
                    # 如果设置为默认环境，先将该项目的其他环境设为非默认
                    if is_default:
                        ApiTestEnvironmentModel.objects.filter(
                            project_id=environment.project_id,
                            is_default=True,
                            deleted_at__isnull=True
                        ).exclude(id=environment_id).update(is_default=False)
                    environment.is_default = is_default
                    update_fields.append('is_default')

                if not update_fields:
                    response["code"] = ErrorCode.PARAM_BLANK
                    response["message"] = "没有需要更新的字段"
                    response["status_code"] = 400
                    return response

                environment.save(update_fields=update_fields)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "更新成功"
            response["data"] = {
                "environment_id": environment.id,
                "env_name": environment.env_name,
                "base_url": environment.base_url
            }

            return response

        except ApiTestEnvironmentModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "环境配置不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["environment_id"])
    def delete_api_test_environment(self, environment_id):
        """
        删除接口测试环境配置（软删除）
        :param environment_id: 环境配置id
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            environment = ApiTestEnvironmentModel.objects.get(id=environment_id, deleted_at__isnull=True)
            environment.deleted_at = timezone.now()
            environment.save(update_fields=['deleted_at'])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "删除成功"
            response["data"] = {
                "environment_id": environment_id
            }

            return response

        except ApiTestEnvironmentModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "环境配置不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    # ==================== 接口测试执行管理 ====================

    @valid_params_blank(required_params_list=["test_case_id", "env_id", "executed_user_id", "executed_user"])
    def execute_api_test_case(self, test_case_id, env_id, executed_user_id, executed_user):
        """
        执行接口测试用例（创建执行记录并提交异步任务）
        :param test_case_id: 测试用例id
        :param env_id: 环境配置id
        :param executed_user_id: 执行人id
        :param executed_user: 执行人
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            # 验证测试用例是否存在
            test_case = ApiTestCaseModel.objects.get(id=test_case_id, deleted_at__isnull=True)

            # 验证环境配置是否存在
            environment = ApiTestEnvironmentModel.objects.get(id=env_id, deleted_at__isnull=True)

            # 创建执行记录
            execution = ApiTestExecutionModel.objects.create(
                test_case_id=test_case_id,
                env_id=env_id,
                status=ApiTestExecutionModel.ExecutionStatus.PENDING,
                trigger_type=ApiTestExecutionModel.TriggerType.MANUAL,
                executed_user_id=executed_user_id,
                executed_user=executed_user
            )

            # 提交异步任务
            task = ApiTestTaskService.executeApiTestTask.delay(execution.id)

            # 更新 Celery 任务 ID
            execution.celery_task_id = task.id
            execution.save(update_fields=['celery_task_id'])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "执行任务已提交"
            response["data"] = {
                "execution_id": execution.id,
                "celery_task_id": task.id,
                "test_case_id": test_case_id,
                "test_case_name": test_case.case_name,
                "env_id": env_id,
                "env_name": environment.env_name,
                "status": execution.status,
                "status_label": execution.get_status_display()
            }

            return response

        except ApiTestCaseModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "测试用例不存在"
            response["status_code"] = 400
            return response

        except ApiTestEnvironmentModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "环境配置不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["execution_id"])
    def get_api_test_execution_status(self, execution_id):
        """
        获取执行任务状态
        :param execution_id: 执行记录id
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            execution = ApiTestExecutionModel.objects.get(id=execution_id)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询成功"
            response["data"] = {
                "execution_id": execution.id,
                "status": execution.status,
                "status_label": execution.get_status_display(),
                "total_cases": execution.total_cases,
                "passed_cases": execution.passed_cases,
                "failed_cases": execution.failed_cases,
                "pass_rate": float(execution.pass_rate) if execution.pass_rate else None,
                "report_url": execution.report_url,
                "error_message": execution.error_message,
                "started_at": timezone.localtime(execution.started_at).strftime("%Y-%m-%d %H:%M:%S") if execution.started_at else None,
                "finished_at": timezone.localtime(execution.finished_at).strftime("%Y-%m-%d %H:%M:%S") if execution.finished_at else None,
                "duration": execution.duration
            }

            return response

        except ApiTestExecutionModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "执行记录不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["page", "page_size"])
    def get_api_test_execution_history(self, page, page_size, test_case_id=None, project_id=None, status=None, trigger_type=None, has_report=None):
        """
        获取执行历史记录列表
        :param page: 页码
        :param page_size: 分页大小
        :param test_case_id: 测试用例id
        :param project_id: 项目id
        :param status: 执行状态
        :param trigger_type: 触发类型
        :param has_report: 是否有报告
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        # 参数校验
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
            filter_map = {}

            if test_case_id:
                filter_map["test_case_id"] = test_case_id

            if project_id:
                # 通过子查询获取项目下的所有用例ID
                case_ids = ApiTestCaseModel.objects.filter(
                    project_id=project_id,
                    deleted_at__isnull=True
                ).values_list('id', flat=True)
                filter_map["test_case_id__in"] = list(case_ids)

            if status is not None:
                filter_map["status"] = status

            if trigger_type is not None:
                filter_map["trigger_type"] = trigger_type

            if has_report:
                filter_map["report_url__isnull"] = False

            query_set = ApiTestExecutionModel.objects.filter(**filter_map).order_by('-created_at')

            # 如果需要有报告的记录，排除空字符串
            if has_report:
                query_set = query_set.exclude(report_url='')

            paginator = Paginator(query_set, page_size)
            page_obj = paginator.get_page(page)

            # 批量获取关联数据，避免 N+1 查询
            execution_list = list(page_obj.object_list)
            test_case_ids = set(obj.test_case_id for obj in execution_list if obj.test_case_id)
            env_ids = set(obj.env_id for obj in execution_list if obj.env_id)

            # 批量查询测试用例
            test_cases_map = {}
            if test_case_ids:
                test_cases = ApiTestCaseModel.objects.filter(id__in=test_case_ids)
                test_cases_map = {tc.id: tc for tc in test_cases}

            # 批量查询环境配置
            environments_map = {}
            if env_ids:
                environments = ApiTestEnvironmentModel.objects.filter(id__in=env_ids)
                environments_map = {env.id: env for env in environments}

            results = []
            for obj in execution_list:
                # 从预加载的数据中获取关联信息
                test_case = test_cases_map.get(obj.test_case_id)
                case_name = test_case.case_name if test_case else None
                case_project_id = test_case.project_id if test_case else None

                environment = environments_map.get(obj.env_id)
                env_name = environment.env_name if environment else None

                item = {
                    "id": obj.id,
                    "test_case_id": obj.test_case_id,
                    "case_name": case_name,
                    "project_id": case_project_id,
                    "env_id": obj.env_id,
                    "env_name": env_name,
                    "status": obj.status,
                    "status_label": obj.get_status_display(),
                    "trigger_type": obj.trigger_type,
                    "trigger_type_label": obj.get_trigger_type_display(),
                    "total_cases": obj.total_cases,
                    "passed_cases": obj.passed_cases,
                    "failed_cases": obj.failed_cases,
                    "pass_rate": float(obj.pass_rate) if obj.pass_rate else None,
                    "report_url": obj.report_url,
                    "started_at": timezone.localtime(obj.started_at).strftime("%Y-%m-%d %H:%M:%S") if obj.started_at else None,
                    "finished_at": timezone.localtime(obj.finished_at).strftime("%Y-%m-%d %H:%M:%S") if obj.finished_at else None,
                    "duration": obj.duration,
                    "executed_user_id": obj.executed_user_id,
                    "executed_user": obj.executed_user,
                    "created_at": timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else None
                }
                results.append(item)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询成功"
            response["data"] = {
                "results": results,
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "page_size": page_size
            }

            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["execution_id"])
    def get_api_test_execution_detail(self, execution_id):
        """
        获取执行记录详情
        :param execution_id: 执行记录id
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            execution = ApiTestExecutionModel.objects.get(id=execution_id)

            # 获取关联的测试用例
            try:
                test_case = ApiTestCaseModel.objects.get(id=execution.test_case_id)
                case_name = test_case.case_name
                case_project_id = test_case.project_id
            except ApiTestCaseModel.DoesNotExist:
                case_name = None
                case_project_id = None

            # 获取关联的环境
            try:
                environment = ApiTestEnvironmentModel.objects.get(id=execution.env_id)
                env_name = environment.env_name
                env_base_url = environment.base_url
            except ApiTestEnvironmentModel.DoesNotExist:
                env_name = None
                env_base_url = None

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询成功"
            response["data"] = {
                "id": execution.id,
                "test_case_id": execution.test_case_id,
                "case_name": case_name,
                "project_id": case_project_id,
                "env_id": execution.env_id,
                "env_name": env_name,
                "env_base_url": env_base_url,
                "status": execution.status,
                "status_label": execution.get_status_display(),
                "trigger_type": execution.trigger_type,
                "trigger_type_label": execution.get_trigger_type_display(),
                "scheduled_task_id": execution.scheduled_task_id,
                "celery_task_id": execution.celery_task_id,
                "total_cases": execution.total_cases,
                "passed_cases": execution.passed_cases,
                "failed_cases": execution.failed_cases,
                "pass_rate": float(execution.pass_rate) if execution.pass_rate else None,
                "report_url": execution.report_url,
                "error_message": execution.error_message,
                "started_at": timezone.localtime(execution.started_at).strftime("%Y-%m-%d %H:%M:%S") if execution.started_at else None,
                "finished_at": timezone.localtime(execution.finished_at).strftime("%Y-%m-%d %H:%M:%S") if execution.finished_at else None,
                "duration": execution.duration,
                "executed_user_id": execution.executed_user_id,
                "executed_user": execution.executed_user,
                "created_at": timezone.localtime(execution.created_at).strftime("%Y-%m-%d %H:%M:%S") if execution.created_at else None,
                "updated_at": timezone.localtime(execution.updated_at).strftime("%Y-%m-%d %H:%M:%S") if execution.updated_at else None
            }

            return response

        except ApiTestExecutionModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "执行记录不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    # ==================== 接口测试定时任务管理 ====================

    @valid_params_blank(required_params_list=[
        "project_id", "task_name", "test_case_id", "env_id",
        "schedule_type", "schedule_time", "created_user_id", "created_user"
    ])
    def create_api_test_schedule(self, project_id, task_name, test_case_id, env_id,
                                  schedule_type, schedule_time, created_user_id, created_user,
                                  description=None, schedule_weekday=None, is_enabled=True):
        """
        创建接口测试定时任务
        :param project_id: 所属项目id
        :param task_name: 任务名称
        :param test_case_id: 测试用例id
        :param env_id: 环境配置id
        :param schedule_type: 调度类型（0-每天，1-每周）
        :param schedule_time: 执行时间
        :param created_user_id: 创建人id
        :param created_user: 创建人
        :param description: 任务描述
        :param schedule_weekday: 执行星期（1-7，仅 weekly 类型使用）
        :param is_enabled: 是否启用
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            # 验证测试用例是否存在
            test_case = ApiTestCaseModel.objects.get(id=test_case_id, deleted_at__isnull=True)

            # 验证环境配置是否存在
            environment = ApiTestEnvironmentModel.objects.get(id=env_id, deleted_at__isnull=True)

            # 验证调度类型
            if schedule_type == ApiTestScheduleModel.ScheduleType.WEEKLY and schedule_weekday is None:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "每周执行类型必须指定执行星期"
                response["status_code"] = 400
                return response

            if schedule_weekday is not None and (schedule_weekday < 1 or schedule_weekday > 7):
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "执行星期必须在 1-7 之间"
                response["status_code"] = 400
                return response

            # 计算下次执行时间
            now = timezone.now()
            local_now = timezone.localtime(now)

            if schedule_type == ApiTestScheduleModel.ScheduleType.DAILY:
                # 今天的执行时间
                if local_now.time() >= schedule_time:
                    # 今天已过执行时间，下次执行是明天
                    next_date = local_now.date() + timedelta(days=1)
                else:
                    next_date = local_now.date()
                next_execution_time = timezone.make_aware(
                    datetime.combine(next_date, schedule_time)
                )
            else:
                # 每周执行
                current_weekday = local_now.isoweekday()
                days_until = (schedule_weekday - current_weekday + 7) % 7
                if days_until == 0 and local_now.time() >= schedule_time:
                    days_until = 7
                next_date = local_now.date() + timedelta(days=days_until)
                next_execution_time = timezone.make_aware(
                    datetime.combine(next_date, schedule_time)
                )

            # 创建定时任务
            schedule = ApiTestScheduleModel.objects.create(
                project_id=project_id,
                task_name=task_name,
                description=description,
                test_case_id=test_case_id,
                env_id=env_id,
                schedule_type=schedule_type,
                schedule_time=schedule_time,
                schedule_weekday=schedule_weekday,
                is_enabled=is_enabled,
                next_execution_time=next_execution_time if is_enabled else None,
                created_user_id=created_user_id,
                created_user=created_user
            )

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "创建成功"
            response["data"] = {
                "schedule_id": schedule.id,
                "task_name": task_name,
                "test_case_name": test_case.case_name,
                "env_name": environment.env_name,
                "next_execution_time": timezone.localtime(next_execution_time).strftime("%Y-%m-%d %H:%M:%S") if next_execution_time else None
            }

            return response

        except ApiTestCaseModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "测试用例不存在"
            response["status_code"] = 400
            return response

        except ApiTestEnvironmentModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "环境配置不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["page", "page_size"])
    def get_api_test_schedule_list(self, page, page_size, project_id=None, task_name=None, is_enabled=None):
        """
        获取定时任务列表
        :param page: 页码
        :param page_size: 分页大小
        :param project_id: 项目id
        :param task_name: 任务名称（模糊查询）
        :param is_enabled: 是否启用
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        # 参数校验
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
                filter_map["project_id"] = project_id

            if task_name:
                filter_map["task_name__contains"] = task_name

            if is_enabled is not None:
                filter_map["is_enabled"] = is_enabled

            query_set = ApiTestScheduleModel.objects.filter(**filter_map).order_by('-created_at')

            paginator = Paginator(query_set, page_size)
            page_obj = paginator.get_page(page)

            # 批量获取关联数据，避免 N+1 查询
            schedule_list = list(page_obj.object_list)
            test_case_ids = set(obj.test_case_id for obj in schedule_list if obj.test_case_id)
            env_ids = set(obj.env_id for obj in schedule_list if obj.env_id)

            # 批量查询测试用例
            test_cases_map = {}
            if test_case_ids:
                test_cases = ApiTestCaseModel.objects.filter(id__in=test_case_ids)
                test_cases_map = {tc.id: tc for tc in test_cases}

            # 批量查询环境配置
            environments_map = {}
            if env_ids:
                environments = ApiTestEnvironmentModel.objects.filter(id__in=env_ids)
                environments_map = {env.id: env for env in environments}

            results = []
            for obj in schedule_list:
                # 从预加载的数据中获取关联信息
                test_case = test_cases_map.get(obj.test_case_id)
                case_name = test_case.case_name if test_case else None

                environment = environments_map.get(obj.env_id)
                env_name = environment.env_name if environment else None

                item = {
                    "id": obj.id,
                    "project_id": obj.project_id,
                    "task_name": obj.task_name,
                    "description": obj.description,
                    "test_case_id": obj.test_case_id,
                    "case_name": case_name,
                    "env_id": obj.env_id,
                    "env_name": env_name,
                    "schedule_type": obj.schedule_type,
                    "schedule_type_label": obj.get_schedule_type_display(),
                    "schedule_time": obj.schedule_time.strftime("%H:%M") if obj.schedule_time else None,
                    "schedule_weekday": obj.schedule_weekday,
                    "is_enabled": obj.is_enabled,
                    "last_execution_time": timezone.localtime(obj.last_execution_time).strftime("%Y-%m-%d %H:%M:%S") if obj.last_execution_time else None,
                    "last_execution_status": obj.last_execution_status,
                    "last_execution_status_label": obj.get_last_execution_status_display() if obj.last_execution_status is not None else None,
                    "next_execution_time": timezone.localtime(obj.next_execution_time).strftime("%Y-%m-%d %H:%M:%S") if obj.next_execution_time else None,
                    "created_user_id": obj.created_user_id,
                    "created_user": obj.created_user,
                    "created_at": timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else None,
                    "updated_at": timezone.localtime(obj.updated_at).strftime("%Y-%m-%d %H:%M:%S") if obj.updated_at else None
                }
                results.append(item)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询成功"
            response["data"] = {
                "results": results,
                "total_count": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "page_size": page_size
            }

            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["schedule_id"])
    def update_api_test_schedule(self, schedule_id, task_name=None, description=None, test_case_id=None,
                                  env_id=None, schedule_type=None, schedule_time=None, schedule_weekday=None):
        """
        更新定时任务配置
        :param schedule_id: 定时任务id
        :param task_name: 任务名称
        :param description: 任务描述
        :param test_case_id: 测试用例id
        :param env_id: 环境配置id
        :param schedule_type: 调度类型
        :param schedule_time: 执行时间
        :param schedule_weekday: 执行星期
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            schedule = ApiTestScheduleModel.objects.get(id=schedule_id, deleted_at__isnull=True)

            update_fields = []
            need_recalc_next_time = False

            if task_name is not None:
                schedule.task_name = task_name
                update_fields.append('task_name')

            if description is not None:
                schedule.description = description
                update_fields.append('description')

            if test_case_id is not None:
                # 验证测试用例是否存在
                ApiTestCaseModel.objects.get(id=test_case_id, deleted_at__isnull=True)
                schedule.test_case_id = test_case_id
                update_fields.append('test_case_id')

            if env_id is not None:
                # 验证环境配置是否存在
                ApiTestEnvironmentModel.objects.get(id=env_id, deleted_at__isnull=True)
                schedule.env_id = env_id
                update_fields.append('env_id')

            if schedule_type is not None:
                schedule.schedule_type = schedule_type
                update_fields.append('schedule_type')
                need_recalc_next_time = True

            if schedule_time is not None:
                schedule.schedule_time = schedule_time
                update_fields.append('schedule_time')
                need_recalc_next_time = True

            if schedule_weekday is not None:
                schedule.schedule_weekday = schedule_weekday
                update_fields.append('schedule_weekday')
                need_recalc_next_time = True

            if not update_fields:
                response["code"] = ErrorCode.PARAM_BLANK
                response["message"] = "没有需要更新的字段"
                response["status_code"] = 400
                return response

            # 重新计算下次执行时间
            if need_recalc_next_time and schedule.is_enabled:
                now = timezone.now()
                local_now = timezone.localtime(now)
                exec_time = schedule.schedule_time

                if schedule.schedule_type == ApiTestScheduleModel.ScheduleType.DAILY:
                    if local_now.time() >= exec_time:
                        next_date = local_now.date() + timedelta(days=1)
                    else:
                        next_date = local_now.date()
                    schedule.next_execution_time = timezone.make_aware(
                        datetime.combine(next_date, exec_time)
                    )
                else:
                    current_weekday = local_now.isoweekday()
                    weekday = schedule.schedule_weekday or 1
                    days_until = (weekday - current_weekday + 7) % 7
                    if days_until == 0 and local_now.time() >= exec_time:
                        days_until = 7
                    next_date = local_now.date() + timedelta(days=days_until)
                    schedule.next_execution_time = timezone.make_aware(
                        datetime.combine(next_date, exec_time)
                    )
                update_fields.append('next_execution_time')

            schedule.save(update_fields=update_fields)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "更新成功"
            response["data"] = {
                "schedule_id": schedule.id,
                "task_name": schedule.task_name,
                "next_execution_time": timezone.localtime(schedule.next_execution_time).strftime("%Y-%m-%d %H:%M:%S") if schedule.next_execution_time else None
            }

            return response

        except ApiTestScheduleModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "定时任务不存在"
            response["status_code"] = 400
            return response

        except ApiTestCaseModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "测试用例不存在"
            response["status_code"] = 400
            return response

        except ApiTestEnvironmentModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "环境配置不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["schedule_id", "is_enabled"])
    def toggle_api_test_schedule(self, schedule_id, is_enabled):
        """
        启用/禁用定时任务
        :param schedule_id: 定时任务id
        :param is_enabled: 是否启用
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            schedule = ApiTestScheduleModel.objects.get(id=schedule_id, deleted_at__isnull=True)

            schedule.is_enabled = is_enabled

            # 如果启用，重新计算下次执行时间
            if is_enabled:
                now = timezone.now()
                local_now = timezone.localtime(now)
                exec_time = schedule.schedule_time

                if schedule.schedule_type == ApiTestScheduleModel.ScheduleType.DAILY:
                    if local_now.time() >= exec_time:
                        next_date = local_now.date() + timedelta(days=1)
                    else:
                        next_date = local_now.date()
                    schedule.next_execution_time = timezone.make_aware(
                        datetime.combine(next_date, exec_time)
                    )
                else:
                    current_weekday = local_now.isoweekday()
                    weekday = schedule.schedule_weekday or 1
                    days_until = (weekday - current_weekday + 7) % 7
                    if days_until == 0 and local_now.time() >= exec_time:
                        days_until = 7
                    next_date = local_now.date() + timedelta(days=days_until)
                    schedule.next_execution_time = timezone.make_aware(
                        datetime.combine(next_date, exec_time)
                    )
            else:
                schedule.next_execution_time = None

            schedule.save(update_fields=['is_enabled', 'next_execution_time'])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "启用成功" if is_enabled else "禁用成功"
            response["data"] = {
                "schedule_id": schedule.id,
                "is_enabled": schedule.is_enabled,
                "next_execution_time": timezone.localtime(schedule.next_execution_time).strftime("%Y-%m-%d %H:%M:%S") if schedule.next_execution_time else None
            }

            return response

        except ApiTestScheduleModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "定时任务不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["schedule_id"])
    def delete_api_test_schedule(self, schedule_id):
        """
        删除定时任务（软删除）
        :param schedule_id: 定时任务id
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            schedule = ApiTestScheduleModel.objects.get(id=schedule_id, deleted_at__isnull=True)
            schedule.deleted_at = timezone.now()
            schedule.save(update_fields=['deleted_at'])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "删除成功"
            response["data"] = {
                "schedule_id": schedule_id
            }

            return response

        except ApiTestScheduleModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "定时任务不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["schedule_id", "executed_user_id", "executed_user"])
    def trigger_api_test_schedule(self, schedule_id, executed_user_id, executed_user):
        """
        手动触发定时任务（立即执行一次）
        :param schedule_id: 定时任务id
        :param executed_user_id: 执行人id
        :param executed_user: 执行人
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            schedule = ApiTestScheduleModel.objects.get(id=schedule_id, deleted_at__isnull=True)

            # 创建执行记录
            execution = ApiTestExecutionModel.objects.create(
                test_case_id=schedule.test_case_id,
                env_id=schedule.env_id,
                status=ApiTestExecutionModel.ExecutionStatus.PENDING,
                trigger_type=ApiTestExecutionModel.TriggerType.MANUAL,
                scheduled_task_id=schedule.id,
                executed_user_id=executed_user_id,
                executed_user=executed_user
            )

            # 提交异步任务
            task = ApiTestTaskService.executeApiTestTask.delay(execution.id)

            # 更新 Celery 任务 ID
            execution.celery_task_id = task.id
            execution.save(update_fields=['celery_task_id'])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "触发成功"
            response["data"] = {
                "execution_id": execution.id,
                "celery_task_id": task.id,
                "schedule_id": schedule_id,
                "task_name": schedule.task_name
            }

            return response

        except ApiTestScheduleModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "定时任务不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response