

from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone
from django.utils.decorators import method_decorator

from constant.error_code import ErrorCode
from functional_test.models.functional_test_case_model import FunctionalTestCaseModel
from project_decorator.request_decorators import valid_params_blank
from projects.models import ProjectModel
from requirements.models import RequirementModel, RequirementDocumentModel
from tasks.functional_test_case_tasks import FunctionalTestCaseTasks


class Service:

    def __init__(self):
        pass

    @valid_params_blank(required_params_list=["project_id", "requirement_id", "case_title", "test_steps", "expected_result", "created_user_id", "created_user"])
    def create_functional_test_case(self, project_id, requirement_id, case_title, test_steps,
                                     expected_result, created_user_id, created_user,
                                     precondition=None, module=None, priority=FunctionalTestCaseModel.PriorityChoices.P0,
                                     comment=None, case_source=FunctionalTestCaseModel.CaseSourceChoices.MANUAL):
        """
        创建功能测试用例
        :param project_id: 所属项目id
        :param requirement_id: 所属需求id
        :param case_title: 用例标题
        :param test_steps: 测试步骤
        :param expected_result: 预期结果
        :param created_user_id: 创建人id
        :param created_user: 创建人
        :param precondition: 前置条件（可选）
        :param module: 所属模块（可选）
        :param priority: 优先级（可选，默认P0, 0-P0, 1-P1, 2-P2, 3-P3）
        :param comment: 备注（可选）
        :param case_source: 用例来源（可选，默认手动创建，支持：0-手动创建，1-AI生成，2-导入）
        :return:
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        try:
            # 校验优先级是否合法
            valid_priority = [choice.value for choice in FunctionalTestCaseModel.PriorityChoices]
            if priority not in valid_priority:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = f"优先级参数无效，必须是以下值之一：{valid_priority} (0-P0, 1-P1, 2-P2, 3-P3)"
                response["status_code"] = 400
                return response

            # 校验用例来源是否合法
            valid_case_sources = [choice.value for choice in FunctionalTestCaseModel.CaseSourceChoices]
            if case_source not in valid_case_sources:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = f"用例来源参数无效，必须是以下值之一：{valid_case_sources} (0-手动创建，1-AI生成，2-导入)"
                response["status_code"] = 400
                return response

            # 校验项目是否存在
            ProjectModel.objects.get(id=project_id, deleted_at__isnull=True)

            # 校验需求是否存在
            RequirementModel.objects.get(id=requirement_id, deleted_at__isnull=True)

            # 创建测试用例
            test_case = FunctionalTestCaseModel.objects.create(
                project_id=project_id,
                requirement_id=requirement_id,
                case_title=case_title,
                precondition=precondition,
                test_steps=test_steps,
                expected_result=expected_result,
                module=module,
                priority=priority,
                comment=comment,
                case_source=case_source,
                created_user_id=created_user_id,
                created_user=created_user
            )

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "创建成功"
            response["data"] = {
                "id": test_case.id,
                "project_id": test_case.project_id,
                "requirement_id": test_case.requirement_id,
                "case_title": test_case.case_title,
                "priority": test_case.priority,
                "case_source": test_case.case_source,
                "created_at": timezone.localtime(test_case.created_at).strftime("%Y-%m-%d %H:%M:%S")
            }
            return response

        except ProjectModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "项目不存在"
            response["status_code"] = 400
            return response

        except RequirementModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "需求不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["page", "page_size"])
    def get_functional_test_case_list(self, page, page_size, test_case_id=None, project_id=None,
                                      case_title=None, module=None, priority=None, case_source=None,
                                      requirement_id=None, execution_status=None, requirement_document_id=None):
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        if not isinstance(page, int) or not isinstance(page_size, int):
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "参数无效"
            response["status_code"] = 400
            return response

        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100

        if ((test_case_id is not None and not isinstance(test_case_id, int))
                or (project_id is not None and not isinstance(project_id, int))
                or (priority is not None and not isinstance(priority, int))
                or (requirement_id is not None and not isinstance(requirement_id, int))
                or (case_source is not None and not isinstance(case_source, int))
                or (execution_status is not None and not isinstance(execution_status, int))
                or (requirement_document_id is not None and not isinstance(requirement_document_id, int))):
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = "参数无效"
                response["status_code"] = 400
                return response

        try:
            filter_map = {
                "deleted_at__isnull": True,
            }

            if test_case_id is not None:
                filter_map["id"] = test_case_id
            if project_id is not None:
                filter_map["project_id"] = project_id
            if case_title is not None:
                filter_map["case_title__contains"] = case_title
            if module:
                filter_map["module__contains"] = module
            if priority is not None:
                filter_map["priority"] = priority
            if case_source is not None:
                filter_map["case_source"] = case_source
            if requirement_id is not None:
                filter_map["requirement_id"] = requirement_id
            if execution_status is not None:
                filter_map["execution_status"] = execution_status
            if requirement_document_id is not None:
                filter_map["requirement_document_id"] = requirement_document_id

            query_set = FunctionalTestCaseModel.objects.filter(**filter_map).order_by('-created_at')
            paginator = Paginator(query_set, page_size)
            page_obj = paginator.get_page(page)
            query_results = page_obj.object_list

            requirement_document_list = []
            for requirement_item in query_results:
                if requirement_item.requirement_document_id:
                    requirement_document_list.append(requirement_item.requirement_document_id)
            # 批量查询需求文档
            requirement_document_obj = RequirementDocumentModel.objects.filter(
                deleted_at__isnull=True,
                id__in=requirement_document_list,
            )
            requirement_document_dict = {}
            for requirement_document_item in requirement_document_obj:
                requirement_document_dict[requirement_document_item.id] = requirement_document_item.doc_name

            results = []
            for test_case_obj in page_obj.object_list:
                test_case_info = {
                    "id": test_case_obj.id,
                    "project_id": test_case_obj.project_id,
                    "requirement_document_id": test_case_obj.requirement_document_id,
                    "requirement_document_name": requirement_document_dict.get(test_case_obj.requirement_document_id,"未知文档"),
                    "case_title": test_case_obj.case_title,
                    "precondition": test_case_obj.precondition,
                    "test_steps": test_case_obj.test_steps,
                    "expected_result": test_case_obj.expected_result,
                    "module": test_case_obj.module,
                    "priority": test_case_obj.priority,
                    "comment": test_case_obj.comment,
                    "case_source": test_case_obj.case_source,
                    "requirement_id": test_case_obj.requirement_id,
                    "execution_status": test_case_obj.execution_status,
                    "created_user_id": test_case_obj.created_user_id,
                    "created_user": test_case_obj.created_user,
                    "created_at": timezone.localtime(test_case_obj.created_at).strftime("%Y-%m-%d %H:%M:%S")
                }

                results.append(test_case_info)

            current_page = page_obj.number
            total_count = paginator.count
            total_pages = paginator.num_pages

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询测试用例成功"
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

    @valid_params_blank(required_params_list=["test_case_id"])
    def get_functional_test_case_detail(self, test_case_id):
        """
        获取功能测试用例详情
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
            test_case_obj = FunctionalTestCaseModel.objects.get(id=test_case_id, deleted_at__isnull=True)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "查询成功"
            response["data"] = {
                "id": test_case_obj.id,
                "project_id": test_case_obj.project_id,
                "case_title": test_case_obj.case_title,
                "precondition": test_case_obj.precondition,
                "test_steps": test_case_obj.test_steps,
                "expected_result": test_case_obj.expected_result,
                "module": test_case_obj.module,
                "priority": test_case_obj.priority,
                "comment": test_case_obj.comment,
                "case_source": test_case_obj.case_source,
                "requirement_id": test_case_obj.requirement_id,
                "execution_status": test_case_obj.execution_status,
                "created_user_id": test_case_obj.created_user_id,
                "created_user": test_case_obj.created_user,
                "created_at": timezone.localtime(test_case_obj.created_at).strftime("%Y-%m-%d %H:%M:%S")
            }
            return response

        except FunctionalTestCaseModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "测试用例不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["test_case_id"])
    def update_functional_test_case(self, test_case_id, case_title=None, precondition=None,
                                    test_steps=None, expected_result=None, module=None, priority=None,
                                    comment=None, execution_status=None):
        """
        更新功能测试用例
        :param test_case_id: 测试用例id（必填）
        :param case_title: 用例标题（可选）
        :param precondition: 前置条件（可选）
        :param test_steps: 测试步骤（可选）
        :param expected_result: 预期结果（可选）
        :param module: 所属模块（可选）
        :param priority: 优先级（可选）
        :param comment: 备注（可选）
        :param execution_status: 执行状态（可选）
        :return:
        """

        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        if all(value is None for value in [case_title, precondition, test_steps, expected_result, module, priority, comment, execution_status]):
            response["code"] = ErrorCode.PARAM_MISSING
            response["message"] = "更新的参数为空"
            response["status_code"] = 400

        try:
            test_case_obj = FunctionalTestCaseModel.objects.get(id=test_case_id, deleted_at__isnull=True)

            updated_fields_list = []

            if case_title is not None:
                test_case_obj.case_title = case_title
                updated_fields_list.append("case_title")

            if precondition is not None:
                test_case_obj.precondition = precondition
                updated_fields_list.append("precondition")

            if test_steps is not None:
                test_case_obj.test_steps = test_steps
                updated_fields_list.append("test_steps")

            if expected_result is not None:
                test_case_obj.expected_result = expected_result
                updated_fields_list.append("expected_result")

            if module is not None:
                test_case_obj.module = module
                updated_fields_list.append("module")

            if priority is not None:
                test_case_obj.priority = priority
                updated_fields_list.append("priority")

            if comment is not None:
                test_case_obj.comment = comment
                updated_fields_list.append("comment")

            if execution_status is not None:
                test_case_obj.execution_status = execution_status
                updated_fields_list.append("execution_status")

            test_case_obj.save(update_fields=updated_fields_list)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "更新成功"
            response["data"] = {
                "id": test_case_obj.id,
                "project_id": test_case_obj.project_id,
                "case_title": test_case_obj.case_title,
                "precondition": test_case_obj.precondition,
                "test_steps": test_case_obj.test_steps,
                "expected_result": test_case_obj.expected_result,
                "module": test_case_obj.module,
                "priority": test_case_obj.priority,
                "comment": test_case_obj.comment,
                "execution_status": test_case_obj.execution_status,
            }
            return response

        except FunctionalTestCaseModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "测试用例不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["test_case_id"])
    def delete_functional_test_case(self, test_case_id):
        """
        删除功能测试用例（软删除）
        :param test_case_id: 测试用例id
        :return:
        """
        response = {
         "code": "",
         "message": "",
         "data": {},
         "status_code": 200
        }

        # 校验参数
        if not isinstance(test_case_id, int):
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "参数无效"
            response["status_code"] = 400
            return response

        try:
            test_case_obj = FunctionalTestCaseModel.objects.get(id=test_case_id, deleted_at__isnull=True)
            test_case_obj.deleted_at = timezone.now()
            test_case_obj.save(update_fields=["deleted_at"])

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "删除成功"
            response["data"]["test_case_id"] = test_case_obj.id
            return response

        except FunctionalTestCaseModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "测试用例不存在"
            response["status_code"] = 400
            return response

        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = f"服务器错误：{str(e)}"
            response["status_code"] = 500
            return response

    @valid_params_blank(required_params_list=["requirement_id_list"])
    def generate_functional_test_case(self, requirement_id_list):
        """
        AI生成功能测试用例
        :param requirement_id_list: 需求项id列表
        :return:
        """
        response = {
         "code": "",
         "message": "",
         "data": {},
         "status_code": 200
        }
        try:

            requirement_obj_list = list(RequirementModel.objects.filter(
                id__in=requirement_id_list,
                deleted_at__isnull=True
            ))
            found_requirement_id_list = []
            for requirement_obj in requirement_obj_list:
                found_requirement_id_list.append(requirement_obj.id)
            miss_requirement_list = []
            for requirement_id in requirement_id_list:
                if requirement_id not in found_requirement_id_list:
                    miss_requirement_list.append(requirement_id)
            if miss_requirement_list:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = f"需求项不存在: {miss_requirement_list}"
                response["status_code"] = 400
                return response

            # 检查状态
            invalid_requirement_id_list = []
            for requirement in requirement_obj_list:
                # 需求项状态不是已审核
                if requirement.status != RequirementModel.RequirementStatus.CONFIRMED.value:
                    invalid_requirement_id_list.append(requirement.id)
            if invalid_requirement_id_list:
                response["code"] = ErrorCode.PARAM_INVALID
                response["message"] = f"需求项状态非已审核：: {invalid_requirement_id_list}"
                response["status_code"] = 400
                return response

            # 更新状态为 生成测试用例中
            RequirementModel.objects.filter(
                id__in=requirement_id_list,
                deleted_at__isnull=True
            ).update(status=RequirementModel.RequirementStatus.GENERATING)

            # 提交异步任务
            FunctionalTestCaseTasks.async_generate_functional_test_case.delay(requirement_id_list)

            response["code"] = ErrorCode.SUCCESS
            response["message"] = "提交生成测试用例任务"
            response["data"]["list"] = requirement_id_list

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

    def get_functional_test_case_module(self):
        """获取所有模块列表及数据"""
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }
        try:
            modules = FunctionalTestCaseModel.objects.filter(
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
        except RequirementModel.DoesNotExist:
            response["code"] = ErrorCode.PARAM_INVALID
            response["message"] = "不存在模块"
            response["status_code"] = 400
            return response
        except Exception as e:
            response["code"] = ErrorCode.SERVER_ERROR
            response["message"] = str(e)
            response["status_code"] = 500
            return response