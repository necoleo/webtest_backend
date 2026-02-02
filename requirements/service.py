import os
from datetime import datetime

from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from qcloud_cos import CosClientError

from constant.error_code import ErrorCode
from functional_test.models.functional_test_case_model import FunctionalTestCaseModel
from project_decorator.request_decorators import valid_params_blank
from projects.models import ProjectModel
from requirements.models import RequirementDocumentModel, RequirementModel, RequirementRelationModel
from requirements.vector.faiss_manager import FaissManager
from requirements.vector.vector_matcher import VectorMatcher
from requirements.vector.vectorization import Vectorization
from tasks.requirement_tasks import RequirementTasks
from utils.cos.cos_client import CosClient


class Service:

    def __init__(self):
        # 本地缓存目录
        self.COS_FILE_SAVED_TEMP = "cos_file_temp"
        self.faiss_manager = FaissManager()
        self.cos_client = CosClient()
        self.vectorization = Vectorization()
        self.tasks = RequirementTasks()
        self.vector_matcher = VectorMatcher()


    @valid_params_blank(required_params_list=["project_id", "version", "file",  "created_user_id", "created_user"])
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
            target_dir = f"webtest/webtest_requirement_document/{project_id}/"
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

    @valid_params_blank(required_params_list=["page", "page_size"])
    def get_requirement_document(self, page, page_size, requirement_document_id=None, project_id=None, doc_name=None, parse_status=None ,version=None):
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

            if parse_status is not None:
                # 精确查询
                filter_map["parse_status"] = parse_status

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

    @valid_params_blank(required_params_list=["requirement_document_id"])
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

        except RequirementDocumentModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "该需求文档不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"错误信息: {str(e)}"
            response['status_code'] = 500
            return response

    @valid_params_blank(required_params_list=["requirement_document_id"])
    def delete_requirement_document(self, requirement_document_id):
        """
        删除需求文档
        :param requirement_document_id:
        :return:
        """

        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        # 校验参数
        if not isinstance(requirement_document_id, int):
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "参数无效"
            response['status_code'] = 400
            return response

        try:
            with transaction.atomic():
                # 删除需求文档
                target_requirement_document = RequirementDocumentModel.objects.get(id=requirement_document_id, deleted_at__isnull=True)
                target_requirement_document.deleted_at = datetime.now()
                target_requirement_document.save()
                # 查询该需求文档关联的已向量化的需求项
                related_requirements_obj = RequirementModel.objects.filter(
                    requirement_document_id=requirement_document_id,
                    deleted_at__isnull=True,
                    is_vectorized=True
                )
                # 待删除向量的需求项列表
                vectorized_requirement_id_list = list(related_requirements_obj.values_list("id", flat=True))
                # 批量删除FAISS向量
                fail_remove_list = []
                for vectorized_requirement_id in vectorized_requirement_id_list:
                    if not self.faiss_manager.remove(vectorized_requirement_id):
                        fail_remove_list.append(vectorized_requirement_id)

                if fail_remove_list:
                    print(f"向量删除失败: {fail_remove_list}")

                # 删除所有关联的需求项
                RequirementModel.objects.filter(
                    requirement_document_id=requirement_document_id,
                    deleted_at__isnull=True
                ).update(deleted_at=datetime.now())

                response["code"] = ErrorCode.SUCCESS
                response["message"] = "删除成功"
                response['data']['requirement_document_id'] = requirement_document_id
                return response

        except RequirementDocumentModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "该需求文档不存在"
            response['status_code'] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response['status_code'] = 500
            return response

    @valid_params_blank(required_params_list=["requirement_document_id", "created_user_id", "created_user"])
    def parse_requirement_document(self, requirement_document_id, created_user_id, created_user):
        """
        异步解析需求文档
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        try:
            requirement_document_obj = RequirementDocumentModel.objects.get(id=requirement_document_id, deleted_at__isnull=True)

            # "解析状态: 0-未解析, 1-解析中, 2-已解析, 3-解析失败"
            if requirement_document_obj.parse_status not in [0, 3]:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "该文件已解析"
                response['status_code'] = 400
                return response

            # 提交异步任务
            task = RequirementTasks.async_parse_requirement_document.delay(requirement_document_id, created_user_id, created_user)

            # 更新状态为解析中
            requirement_document_obj.parse_status = 1
            requirement_document_obj.save(update_fields=["parse_status"])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = f"解析任务已提交，请稍后查看结果"
            response['data'] = {
                "requirement_document_id": requirement_document_id,
                "task_id": task.id
            }
            response["status_code"] = 200

            return response
        except Exception as e:

            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"解析需求文档失败：{str(e)}"
            response['status_code'] = 500
            return response

    @valid_params_blank(required_params_list=["requirement_id"])
    def delete_requirement(self, requirement_id):
        """
         删除需求项
         :param requirement_id:
         :return:
         """

        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        # 校验参数
        if not isinstance(requirement_id, int):
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "参数无效"
            response['status_code'] = 400
            return response

        try:
            with transaction.atomic():
                # 删除需求项
                target_requirement_obj = RequirementModel.objects.get(id=requirement_id, deleted_at__isnull=True)
                target_requirement_obj.deleted_at = datetime.now()
                target_requirement_obj.save()

                # 更新所属需求文档的需求项数量 -1
                RequirementDocumentModel.objects.filter(
                    id=target_requirement_obj.requirement_document_id,
                    deleted_at__isnull=True
                ).update(requirement_count=F('requirement_count') - 1)

                # 删除该需求项关联的FAISS向量
                if target_requirement_obj.is_vectorized == True:
                    self.faiss_manager.remove(target_requirement_obj.id)

                # 删除该需求项的关联关系
                RequirementRelationModel.objects.filter(
                    Q(source_requirement_id=target_requirement_obj.id) |
                    Q(target_requirement_id=target_requirement_obj.id),
                    deleted_at__isnull=True
                ).update(deleted_at=timezone.now())

                # 删除该需求项相关的测试用例
                FunctionalTestCaseModel.objects.filter(
                        requirement_id=target_requirement_obj.id,
                        deleted_at__isnull=True
                ).update(deleted_at=timezone.now())

                response["code"] = ErrorCode.SUCCESS
                response["message"] = "删除成功"
                response['data']['requirement_id'] = requirement_id
                return response

        except RequirementModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "该需求项不存在"
            response['status_code'] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response['status_code'] = 500
            return response

    @valid_params_blank(required_params_list=["page","page_size"])
    def get_requirement(self,page,page_size,requirement_id=None, project_id=None, requirement_document_id=None,
                        requirement_title=None, requirement_content=None, module=None, status=None, is_vectorized=None):
        """
        获取需求项
        :param page: 页码（必填）
        :param page_size: 分页大小（必填）
        :param requirement_id: 需求项id
        :param project_id:  所属项目id
        :param requirement_document_id: 所属需求文档id
        :param requirement_title:   需求项标题
        :param requirement_content: 需求项内容
        :param module:  需求项模块
        :param status:  需求项状态
        :param is_vectorized:   需求项是否向量化
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

            if requirement_id is not None:
                # 精准查询
                filter_map["id"] = requirement_id

            if project_id is not None:
                # 精准查询
                filter_map["project_id"] = project_id

            if requirement_document_id is not None:
                # 精准查询
                filter_map["requirement_document_id"] = requirement_document_id

            if requirement_title is not None:
                # 模糊查询
                filter_map["requirement_title__contains"] = requirement_title

            if requirement_content is not None:
                # 模糊查询
                filter_map["requirement_content__contains"] = requirement_content

            if module is not None:
                # 模糊查询
                filter_map["module__contains"] = module

            if status is not None:
                # 精确查询
                filter_map["status"] = status


            if is_vectorized is not None:
                # 精确查询
                filter_map["is_vectorized"] = is_vectorized


            query_set = RequirementModel.objects.filter(**filter_map).order_by('-created_at')

            paginator = Paginator(query_set, page_size)
            page_obj = paginator.get_page(page)

            query_results = page_obj.object_list
            results = []
            for requirement_obj in query_results:
                requirement_info = {
                    "id": requirement_obj.id,
                    "project_id": requirement_obj.project_id,
                    "requirement_document_id": requirement_obj.requirement_document_id,
                    "requirement_title": requirement_obj.requirement_title,
                    "requirement_content": requirement_obj.requirement_content,
                    "module": requirement_obj.module,
                    "status": requirement_obj.status,
                    "is_vectorized": requirement_obj.is_vectorized,
                    "created_at": requirement_obj.created_at,
                    "updated_at": requirement_obj.updated_at
                }
                if requirement_info["created_at"]:
                    requirement_info["created_at"] = requirement_info["created_at"].strftime(
                        "%Y-%m-%d %H:%M:%S")
                if requirement_info["updated_at"]:
                    requirement_info["updated_at"] = requirement_info["updated_at"].strftime(
                        "%Y-%m-%d %H:%M:%S")

                results.append(requirement_info)

            current_page = page_obj.number
            total_count = paginator.count
            total_pages = paginator.num_pages

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询需求项成功"
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

    @valid_params_blank(required_params_list=["requirement_id"])
    def update_requirement(self, requirement_id, requirement_title=None, requirement_content=None, module=None):
        """
        编辑需求项（只有待审核的需求项才能编辑）
        :param requirement_id: 需求项id，必填
        :param requirement_title: 需求项标题，可选
        :param requirement_content: 需求项内容，可选
        :param module: 需求项所属模块，可选
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        if requirement_title is None and requirement_content is None and module is None:
            response["code"] = ErrorCode.PARAM_BLANK
            response["message"] = "参数为空"
            response['status_code'] = 400
            return response

        try:
            requirement_obj = RequirementModel.objects.get(id=requirement_id, deleted_at__isnull=True)

            if not requirement_obj:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "该需求不存在"
                response['status_code'] = 400
                return response

            if requirement_obj.status != RequirementModel.RequirementStatus.PENDING:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = f"只有待审核的需求项才能编辑，当前状态: {requirement_obj.get_status_display()}"
                response['status_code'] = 400
                return response

            update_fields_list = []
            if requirement_title:
                requirement_obj.requirement_title = requirement_title
                update_fields_list.append("requirement_title")
            if requirement_content:
                requirement_obj.requirement_content = requirement_content
                update_fields_list.append("requirement_content")
            if module:
                requirement_obj.module = module
                update_fields_list.append("module")

            requirement_obj.save(update_fields=update_fields_list)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "更新成功"
            response["data"] = {
                "requirement_id": requirement_obj.id,
                "requirement_title": requirement_obj.requirement_title,
                "requirement_content": requirement_obj.requirement_content,
                "module": requirement_obj.module
            }
            return response

        except RequirementModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "该需求项不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"错误信息: {str(e)}"
            response['status_code'] = 500
            return response

    @valid_params_blank(required_params_list=["project_id","requirement_document_id", "requirement_content", "created_user_id", "created_user"])
    def upload_requirement(self, project_id, requirement_document_id, requirement_title,
                           requirement_content, module, created_user_id, created_user):
        """
        上传需求项
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            # 校验该项目是否存在
            project_obj = ProjectModel.objects.get(id=project_id, deleted_at__isnull=True)
            # 校验该需求文档是否存在
            requirement_document_obj = RequirementDocumentModel.objects.get(
                id=requirement_document_id,
                project_id=project_id,
                deleted_at__isnull=True
            )
            with transaction.atomic():
                # 创建需求项
                requirement_obj = RequirementModel.objects.create(
                    project_id=project_id,
                    requirement_document_id=requirement_document_id,
                    requirement_title=requirement_title,
                    requirement_content=requirement_content,
                    module=module,
                    created_user_id=created_user_id,
                    created_user=created_user,
                )

                # 更新需求文档解析需求项数量 +1
                current_count = requirement_document_obj.requirement_count or 0
                requirement_document_obj.requirement_count = current_count + 1
                requirement_document_obj.save(update_fields=["requirement_count"])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "需求项创建成功"
            response["data"] = {
                "id": requirement_obj.id,
                "project_id": requirement_obj.project_id,
                "requirement_id": requirement_obj.id,
                "requirement_title": requirement_obj.requirement_title,
                "requirement_content": requirement_obj.requirement_content,
                "module": requirement_obj.module,
                "status": requirement_obj.status,
                "is_vectorized": requirement_obj.is_vectorized,
                "created_user_id": requirement_obj.created_user_id,
                "created_user": requirement_obj.created_user,
                "created_at":  requirement_obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            return response
        except ProjectModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "不存在该项目"
            response["status_code"] = 400
            return response

        except RequirementDocumentModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "不存在该需求文档"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = str(e)
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["requirement_id_list"])
    def audit_requirement(self, requirement_id_list):
        """
        审核需求项
        支持批量, 状态变更为处理中，异步触发向量化，完成后更新为已审核
        :param: requirement_id_list 需求项id列表
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        try:
            if not isinstance(requirement_id_list, list) or len(requirement_id_list) < 1:
                response["code"] = ErrorCode.PARAM_MISSING
                response["message"] = "需求项参数为空"
                response["status_code"] = 400
                return response

            process_list = []
            for requirement_id in requirement_id_list:
                requirement_obj = RequirementModel.objects.get(id=requirement_id, deleted_at__isnull=True)
                # 存在非待审核状态的需求项
                if requirement_obj.status != RequirementModel.RequirementStatus.PENDING:
                    response["code"] = ErrorCode.PARAM_INVALID
                    response["message"] = "存在非待审核状态的需求项"
                    response["status_code"] = 400
                    return response

                # 状态更新为 处理中
                requirement_obj.status = RequirementModel.RequirementStatus.PROCESSING
                requirement_obj.save(update_fields=["status"])
                process_list.append(
                    {
                        "id": requirement_obj.id,
                        "message": "审核提交成功，处理中"
                    }
                )

            # 提交异步任务
            if process_list:
                process_requirement_id_list = []
                for process in process_list:
                    process_requirement_id_list.append(process["id"])

                RequirementTasks.async_vectorize_requirement_list.delay(process_requirement_id_list)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "审核提交成功"
            response["data"]["list"] = process_list
            return response
        except RequirementModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "该需求项不存在"
            response["status_code"] = 400
            return response
        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = str(e)
            response["status_code"] = 500
            return response


    @valid_params_blank(required_params_list=["requirement_id_list"])
    def build_similar_relations(self, requirement_id_list):
        """为需求项列表建立双向相似关联"""
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        relation_list = []
        try:
            for requirement_id in requirement_id_list:
                similarity_threshold = float(os.environ.get("SIMILARITY_THRESHOLD"))
                match_number = int(os.environ.get("MATCH_NUMBER"))
                # 获取与requirement_id相似的需求项
                similar_requirements_list = self.vector_matcher.find_similar_by_requirement_id(requirement_id, similarity_threshold, match_number)

                for similar_requirement in similar_requirements_list:
                    similar_requirement_id = similar_requirement["id"]
                    similarity_score = similar_requirement["similarity_score"]

                    # 正向关联
                    if not RequirementRelationModel.objects.filter(
                        source_requirement_id=requirement_id,
                        target_requirement_id=similar_requirement_id,
                        deleted_at__isnull=True
                    ).exists():
                        relation_list.append(
                            RequirementRelationModel(
                                source_requirement_id=requirement_id,
                                target_requirement_id=similar_requirement_id,
                                similarity_score=similarity_score,
                                match_method="vector"
                            )
                        )

                    # 反向关联
                    if not RequirementRelationModel.objects.filter(
                        source_requirement_id=similar_requirement_id,
                        target_requirement_id=requirement_id,
                        deleted_at__isnull=True
                    ).exists():
                        relation_list.append(
                            RequirementRelationModel(
                                source_requirement_id=similar_requirement_id,
                                target_requirement_id=requirement_id,
                                similarity_score=similarity_score,
                                match_method="vector"
                            )
                        )
            if relation_list:
                RequirementRelationModel.objects.bulk_create(relation_list, ignore_conflicts=True)

            # 将模型对象转换为可序列化的字典格式
            serializable_list = [
                {
                    "source_requirement_id": r.source_requirement_id,
                    "target_requirement_id": r.target_requirement_id,
                    "similarity_score": r.similarity_score,
                    "match_method": r.match_method
                }
                for r in relation_list
            ]

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "需求项建立相似关联成功"
            response["data"]["list"] = serializable_list
            return response

        except Exception as e:

            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = str(e)
            response["status_code"] = 500
            return response