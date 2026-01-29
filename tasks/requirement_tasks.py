# -*- coding: utf-8 -*-
"""
需求相关异步任务
包含需求文档解析、需求向量化等任务
"""
import os.path
import sys

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction

from constant.error_code import ErrorCode
from requirements.models import RequirementDocumentModel, RequirementModel
from requirements.parser.requirement_document_parser import RequirementDocumentParser
from requirements.parser.requirement_extractor import RequirementExtractor

from requirements.vector.vectorization import Vectorization
from utils.cos.cos_client import CosClient

logger = get_task_logger(__name__)

# 添加项目根目录到 python 路径
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

class RequirementTasks:
    """需求相关任务"""

    # 本地缓存目录
    COS_FILE_SAVED_TEMP = "cos_file_temp"

    @staticmethod
    @shared_task(bind=True, max_retries=3, default_retry_delay=60)
    def async_parse_requirement_document(task, requirement_document_id, created_user_id, created_user):
        """
        异步解析需求文档任务
        :param task: celery 任务实例
        :param requirement_document_id: 需求文档id
        """

        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        local_path = None


        try:
            # 获取需求文档
            requirement_document_obj = RequirementDocumentModel.objects.get(
                id=requirement_document_id,
                deleted_at__isnull=True
            )

            # 检查状态是否为解析中
            if requirement_document_obj.parse_status != 1:
                logger.warning(
                    f"需求文档 {requirement_document_id} 状态异常."
                    f"当前状态：{requirement_document_obj.parse_status}"
                )
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = f"文档状态异常, 当前状态: {requirement_document_obj.parse_status}"
                response["status_code"] = 400
                return response

            logger.info(f"开始解析需求文档: {requirement_document_id}")

            # 从cos下载文件
            cos_client = CosClient()
            content = cos_client.download_and_read_text_by_url(
                requirement_document_obj.cos_access_url,
                RequirementTasks.COS_FILE_SAVED_TEMP
            )
            logger.info(f"文件下载成功,内容为 {content}")

            # 使用AI提取需求项
            requirement_extractor = RequirementExtractor()
            requirement_list = requirement_extractor.extract_requirement_document(content)
            logger.info(f"AI 提取完成，共提取 {len(requirement_list)} 个需求项")

            # 批量保存到数据库
            with transaction.atomic():
                requirement_model_list = []
                for requirement in requirement_list:
                    requirement_model = RequirementModel(
                        project_id=requirement_document_obj.project_id,
                        requirement_document_id=requirement_document_obj.id,
                        requirement_title=requirement.get("requirement_title"),
                        requirement_content=requirement.get("requirement_content"),
                        created_user_id=created_user_id,
                        created_user=created_user,
                    )
                    requirement_model_list.append(requirement_model)

                RequirementModel.objects.bulk_create(requirement_model_list)

                requirement_document_obj.requirement_count = len(requirement_list)
                requirement_document_obj.parse_status = 2 # 已解析
                requirement_document_obj.save(update_fields=["requirement_count","parse_status"])

            logger.info(
                f"需求文档 {requirement_document_id} 解析完成，"
                f"成功导入 {len(requirement_list)} 个需求"
            )

            response["code"] = ErrorCode.SUCCESS
            response["message"] = f"解析完成，成功导入 {len(requirement_list)} 个需求"
            response["data"] = {
                "requirement_document_id": requirement_document_id,
                "count": len(requirement_list)
            }
            return response

        except RequirementDocumentModel.DoesNotExist:
            logger.error(f"需求文档不存在: {requirement_document_id}")
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "需求文档不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            logger.error(f"需求文档 {requirement_document_id} 解析失败: {str(e)}")

            # 更新状态为"解析失败"
            RequirementTasks.update_parse_status_to_failed(
                requirement_document_id,
                str(e)
            )

            # 重试机制
            if task and task.request.retries < task.max_retries:
                logger.info(
                    f"准备重试，当前第 {task.request.retries + 1} 次，"
                    f"最大重试 {task.max_retries} 次"
                )
                raise task.retry(exc=e)

            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"解析失败: {str(e)}"
            response["status_code"] = 500
            return response

        finally:
            # 清理缓存文件
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                    logger.info(f"缓存文件已清理: {local_path}")
                except Exception as e:
                    logger.warning(f"清理缓存文件失败: {e}")

    @staticmethod
    def update_parse_status_to_failed(requirement_document_id, error_message):
        """
        更新需求文档解析状态为失败
        :param requirement_document_id: 需求文档 ID
        :param error_message: 错误信息
        """
        try:
            RequirementDocumentModel.objects.filter(
                id=requirement_document_id
            ).update(
                parse_status=3  # 解析失败
            )
            logger.info(f"需求文档 {requirement_document_id} 状态已更新为解析失败")
        except Exception as e:
            logger.error(f"更新解析状态失败: {e}")

    @staticmethod
    @shared_task(bind=True, max_retries=3, default_retry_delay=30)
    def async_vectorize_requirement_list(task, requirement_id_list):
        """
        异步向量化指定需求项列表, 并关联需求项
        处理成功：状态 -> 已审核， is_vectorized = True
        处理失败: 状态 -> 待审核
        :param task: celery 任务实例
        :param requirement_id_list 需求项id列表
        """

        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        from requirements.service import Service
        service = Service()
        logger.info(f"开始处理 {len(requirement_id_list)} 个需求项：{requirement_id_list}")
        success_list = []
        fail_list = []
        try:
            # 批量向量化
            vectorization = Vectorization()
            results = vectorization.batch_vectorize_requirement(requirement_id_list)

            # 根据结果更新状态
            for item in results["result"]:
                requirement_id = item["requirement_id"]
                if item["result"]:
                    # 将状态更新为已审核
                    RequirementModel.objects.filter(id=requirement_id).update(
                        status=RequirementModel.RequirementStatus.CONFIRMED,
                        is_vectorized=True
                    )
                    success_list.append(requirement_id)
                else:
                    # 将状态回退至待审核
                    RequirementModel.objects.filter(id=requirement_id).update(
                        status=RequirementModel.RequirementStatus.PENDING
                    )
                    fail_list.append(requirement_id)
                    logger.warning(f"需求项 {requirement_id} 向量化失败：{item.get('message')}")

            # 向量化完成后，建立双向相似关联
            relations_count = 0
            relations_list = []
            if success_list:
                service_response = service.build_similar_relations(success_list)
                relations_count = len(service_response['data']['list'])
                relations_list = service_response['data']['list']

            logger.info(f"批量处理完成，成功 {results['success_count']} 个， 失败 {results['fail_count']} 个, 关联 {relations_count}")

            response["code"] = ErrorCode.SUCCESS
            response["message"] = f"处理完成，成功 {len(success_list)} 个，失败 {len(fail_list)} 个"
            response["data"] = {
                "success_count": len(success_list),
                "fail_count": len(fail_list),
                "relations_list": relations_list
            }
            return response

        except Exception as e:
            logger.error(f"批量处理任务异常: {str(e)}")

            # 重试
            if task and task.request.retries < task.max_retries:
                logger.info(f"准备重试，当前第 {task.request.retries + 1} 次")
                raise task.retry(exc=e)

            # 重试失败，回滚状态
            RequirementModel.objects.filter(
                id__in=requirement_id_list,
                status=RequirementModel.RequirementStatus.PROCESSING
            ).update(status=RequirementModel.RequirementStatus.PENDING)

            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"处理失败：{str(e)}"
            response["status_code"] = 500
            return response
