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
    @shared_task(bind=True, max_retries=3, default_retry_delay=60)
    def async_generate_functional_test_case(task, requirement_id_list):
        """AI生成测试用例"""
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        try:
            logger.info(f"开始为 {len(requirement_id_list)} 个需求项生成测试用例")
            # 逐个需求项生成测试用例
            success_list = []
            fail_list = []
            for requirement_id in requirement_id_list:
                try:
                    requirement_service = Service()
                    requirement_details_response = requirement_service.get_requirement_with_relations(requirement_id)
                    if requirement_details_response["code"] != ErrorCode.SUCCESS:
                        logger.warning(f"需求项 {requirement_id} 获取失败: {requirement_details_response['message']}")
                        fail_list.append(requirement_id)
                        continue

                    requirement_content = requirement_details_response["data"]["requirement_content"]
                    relation_list = requirement_details_response["data"]["relation_requirement_detail_list"]

                    # 调用AI生成测试用例
                    test_case_generator = DifyClient()
                    test_case_list = test_case_generator.get_test_case(requirement_content, relation_list)
                    logger.info(f"AI 生成测试用例完成，共生成 {len(test_case_list)} 条测试用例")

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

                        success_list.append(requirement_id)
                        logger.info(f"需求项 {requirement_id} 保存成功，共 {len(test_case_model_list)} 条用例")

                except Exception as e:
                    logger.error(f"需求项 {requirement_id} 处理异常: {str(e)}")
                    fail_list.append(requirement_id)

            # 3. 处理失败的需求项，回退状态为已审核
            if fail_list:
                FunctionalTestCaseTasks.update_requirement_status_to_confirmed(fail_list)
                logger.info(f"已将 {len(fail_list)} 个失败的需求项状态回退为已审核")

            logger.info(f"生成完成，成功 {len(success_list)} 个，失败 {len(fail_list)} 个")

            response["code"] = ErrorCode.SUCCESS
            response["message"] = f"生成完成，成功 {len(success_list)} 个，失败 {len(fail_list)} 个"
            response["data"] = {
                "success_count": len(success_list),
                "fail_count": len(fail_list),
                "success_list": success_list,
                "fail_list": fail_list
            }
            return response

        except Exception as e:
            logger.error(f"生成测试用例任务异常: {str(e)}")

            # 更新所有需求项状态为已审核（回滚）
            FunctionalTestCaseTasks.update_requirement_status_to_confirmed(requirement_id_list)

            # 重试机制
            if task and task.request.retries < task.max_retries:
                logger.info(
                    f"准备重试，当前第 {task.request.retries + 1} 次，"
                    f"最大重试 {task.max_retries} 次"
                )
                raise task.retry(exc=e)

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

