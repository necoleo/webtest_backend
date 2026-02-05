import os
import sys

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction

from constant.error_code import ErrorCode
from functional_test.ai_generator.dify_client import DifyClient
from functional_test.models.functional_test_case_model import FunctionalTestCaseModel
from requirements.models import RequirementModel, RequirementRelationModel
from requirements.service import Service

logger = get_task_logger(__name__)

# 添加项目根目录到 python 路径
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

class FunctionalTestCaseTasks:
    """功能测试用例相关任务"""

    @staticmethod
    @shared_task(bind=True)
    def async_generate_functional_test_case(task, requirement_id_list):
        """
        派发测试用例生成任务(调度任务)
        将每个需求项拆分为独立的子任务执行，避免超时
        """
        logger.info(f"开始派发 {len(requirement_id_list)} 个需求项的测试用例生成任务")

        dispatched_count = 0
        for requirement_id in requirement_id_list:
            # 派发子任务
            FunctionalTestCaseTasks.generate_single_functional_test_case.delay(requirement_id)
            dispatched_count += 1

        logger.info(f"已派发 {dispatched_count} 个子任务")

        return {
            "code": ErrorCode.SUCCESS,
            "message": f"已派发 {dispatched_count} 个测试用例生成任务",
            "data": {
                "dispatched_count": dispatched_count,
                "requirement_id_list": requirement_id_list
            },
            "status_code": 200
        }

    @staticmethod
    @shared_task(
        bind=True,
        max_retries=3,
        default_retry_delay=60,
        time_limit=300,             # 硬超时 300 s
        soft_time_limit=280,        # 软超时 280 s
        rate_limit='10/m'
    )
    def generate_single_functional_test_case(task, requirement_id):
        """
        AI生成测试用例
        """
        logger.info(f"开始为需求项 {requirement_id} 生成测试用例")
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        try:
            requirement_service = Service()
            requirement_details_response = requirement_service.get_requirement_with_relations(requirement_id)
            if requirement_details_response["code"] != ErrorCode.SUCCESS:
                # 回退状态为已审核
                FunctionalTestCaseTasks.update_single_requirement_status(
                    requirement_id,
                    RequirementModel.RequirementStatus.CONFIRMED
                )
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "需求项获取失败"
                response["status_code"] = 400
                return response

            requirement_content = requirement_details_response["data"]["requirement_content"]
            relation_list = requirement_details_response["data"]["relation_requirement_detail_list"]

            # 调用AI生成测试用例
            test_case_generator = DifyClient()
            test_case_list = test_case_generator.get_test_case(requirement_content, relation_list)
            logger.info(f"需求项 {requirement_id}: AI 生成测试用例完成，共生成 {len(test_case_list)} 条测试用例")

            # 批量保存到数据库
            with transaction.atomic():
                test_case_model_list = []
                requirement_obj = RequirementModel.objects.get(id=requirement_id)
                for test_case in test_case_list:
                    test_case_model = FunctionalTestCaseModel(
                        project_id=requirement_obj.project_id,
                        case_title=test_case["case_title"],
                        precondition=test_case["precondition"],
                        test_steps=test_case["test_steps"],
                        expected_result=test_case["expected_result"],
                        module=test_case["module"],
                        priority=test_case["priority"],
                        comment=test_case["comment"],
                        case_source=FunctionalTestCaseModel.CaseSourceChoices.AI_GENERATED,
                        requirement_id=requirement_id
                    )
                    test_case_model_list.append(test_case_model)
                FunctionalTestCaseModel.objects.bulk_create(test_case_model_list)

                RequirementModel.objects.filter(
                    id=requirement_id,
                    deleted_at__isnull=True
                ).update(status=RequirementModel.RequirementStatus.COVERED)

            logger.info(f"需求项 {requirement_id} 保存成功，共 {len(test_case_model_list)} 条用例")

            response["code"] = ErrorCode.SUCCESS
            response["message"] = f"生成测试用例成功"
            response["data"] = {
                "requirement_id": requirement_id,
                "test_case_count": len(test_case_model_list),
            }
            return response
        except Exception as e:
            logger.error(f"需求项 {requirement_id} 处理异常: {str(e)}")

            # 重试机制
            if task and task.request.retries < task.max_retries:
                logger.info(f"需求项 {requirement_id} 准备重试，当前第 {task.request.retries + 1} 次")
                raise task.retry(exc=e)
            # 重试耗尽，回退状态为已审核
            FunctionalTestCaseTasks.update_single_requirement_status(
                requirement_id,
                RequirementModel.RequirementStatus.CONFIRMED
            )
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"生成失败: {str(e)}"
            response["status_code"] = 500
            return response

    @staticmethod
    def update_requirement_status_to_confirmed(requirement_id_list):
        """
        将需求项状态回退为已审核
        :param requirement_id_list: 需求项 ID 列表
        """
        try:
            RequirementModel.objects.filter(
                id__in=requirement_id_list,
                status=RequirementModel.RequirementStatus.GENERATING
            ).update(status=RequirementModel.RequirementStatus.CONFIRMED)
            logger.info(f"需求项 {requirement_id_list} 状态已回退为已审核")
        except Exception as e:
            logger.error(f"回退需求项状态失败: {e}")


    @staticmethod
    def update_single_requirement_status(requirement_id, status):
        """
        更新单个需求项状态
        :param requirement_id: 需求项 ID
        :param status: 目标状态
        """
        try:
            RequirementModel.objects.filter(
                id=requirement_id,
                deleted_at__isnull=True
            ).update(status=status)
            logger.info(f"需求项 {requirement_id} 状态已更新为 {status}")
        except Exception as e:
            logger.error(f"更新需求项 {requirement_id} 状态失败: {e}")
