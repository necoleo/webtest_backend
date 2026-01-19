# -*- coding: utf-8 -*-
"""
接口测试相关异步任务
包含测试执行、AI 生成用例等任务
"""
import os
import sys
import shutil
import tempfile
import time
from datetime import datetime

import yaml
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

# 使用 Celery 任务日志
logger = get_task_logger(__name__)

# 添加项目根目录到 Python 路径
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
API_AUTO_TEST_DIR = os.path.join(PROJECT_ROOT, 'api_auto_test')

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if API_AUTO_TEST_DIR not in sys.path:
    sys.path.insert(0, API_AUTO_TEST_DIR)

from api_auto_test.models import (
    ApiTestExecutionModel,
    ApiTestCaseModel,
    ApiTestEnvironmentModel
)
from utils.cos.cos_client import CosClient
from utils.report.html_report_generator import HtmlReportGenerator
from constant.error_code import ErrorCode


@shared_task(bind=True, max_retries=3)
def execute_api_test_task(self, execution_id: int) -> dict:
    """
    执行接口测试任务

    流程：
    1. 从数据库获取执行记录和相关配置
    2. 从 COS 下载 YAML 测试用例文件
    3. 解析环境配置，覆盖 YAML 中的 config
    4. 使用 YAMLTestRunner 执行测试，收集每个步骤的详细请求/响应信息
    5. 生成自制 HTML 报告（单文件，包含所有 CSS/JS）
    6. 将报告上传到 COS
    7. 更新执行记录状态

    :param execution_id: 执行记录 ID
    :return: 执行结果（与 Service 层响应格式一致）
    """
    # 响应格式与 Service 层保持一致
    response = {
        "code": "",
        "message": "",
        "data": {},
        "status_code": 200
    }

    temp_dir = None

    try:
        # 1. 获取执行记录
        execution = ApiTestExecutionModel.objects.get(id=execution_id)
        execution.status = ApiTestExecutionModel.ExecutionStatus.RUNNING
        execution.started_at = timezone.now()
        execution.save(update_fields=['status', 'started_at'])

        # 获取测试用例和环境配置
        test_case = ApiTestCaseModel.objects.get(id=execution.test_case_id, deleted_at__isnull=True)
        environment = ApiTestEnvironmentModel.objects.get(id=execution.env_id, deleted_at__isnull=True)

        # 2. 创建临时目录并从 COS 下载 YAML 文件
        temp_dir = tempfile.mkdtemp(prefix='api_test_')
        cos_client = CosClient()

        # 下载 YAML 文件
        yaml_filename = os.path.basename(test_case.cos_access_url.split('?')[0])
        yaml_path = os.path.join(temp_dir, yaml_filename)

        # 解析 COS Key
        cos_key = test_case.cos_access_url.split('.com/')[-1].split('?')[0]
        cos_client.client.download_file(
            Bucket=cos_client.bucket,
            Key=cos_key,
            DestFilePath=yaml_path
        )

        # 3. 加载 YAML 并覆盖环境配置
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)

        # 确保 config 存在
        if 'config' not in yaml_data:
            yaml_data['config'] = {}

        # 覆盖环境配置
        yaml_data['config']['base_url'] = environment.base_url
        if environment.timeout:
            yaml_data['config']['timeout'] = environment.timeout
        if environment.headers:
            yaml_data['config']['headers'] = environment.headers
        
        # 合并环境变量到 config（支持嵌套结构如 credentials、test_data）
        if environment.variables:
            for key, value in environment.variables.items():
                yaml_data['config'][key] = value

        # 保存修改后的 YAML
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False)

        # 4. 直接使用 YAMLTestRunner 执行测试（收集详细信息）
        logger.info(f"开始执行测试，YAML 路径: {yaml_path}")
        
        # 导入测试运行器
        from src.test_cases_parser import YAMLTestRunner
        
        # 切换工作目录
        original_cwd = os.getcwd()
        os.chdir(API_AUTO_TEST_DIR)
        
        try:
            # 初始化运行器
            runner = YAMLTestRunner(yaml_path)
            cases = runner.get_cases()
            total_cases = len(cases)
            
            # 初始化报告生成器
            report_generator = HtmlReportGenerator()
            report_generator.set_test_info(
                name=test_case.case_name,
                environment=environment.env_name,
                base_url=environment.base_url
            )
            
            execution_start = datetime.now()
            passed_cases = 0
            failed_cases = 0
            
            # 执行每个用例并收集详细信息
            for case in cases:
                case_id = case.get('case', 'UNKNOWN')
                case_name = case.get('name', case_id)
                
                logger.info(f"执行用例: {case_id} - {case_name}")
                
                case_start = time.time()
                case_result = {
                    'case_id': case_id,
                    'case_name': case_name,
                    'status': 'PASS',
                    'duration': 0,
                    'error_message': '',
                    'steps': []
                }
                
                try:
                    # 重置变量处理器
                    runner.var_handler = runner.var_handler.__class__(runner.config)
                    
                    # 执行每个步骤
                    for step in case.get('steps', []):
                        step_name = step.get('name', 'unknown_step')
                        step_type = step.get('type', 'http_request')
                        
                        step_result = {
                            'name': step_name,
                            'status': 'PASS',
                            'error_message': '',
                            'request': {},
                            'response': {}
                        }
                        
                        try:
                            # 准备请求
                            request_config = runner.var_handler.replace_variables(step.get('request', {}))
                            
                            # 记录请求信息
                            method = request_config.get('method', 'GET')
                            endpoint = request_config.get('endpoint', '')
                            full_url = runner.config.get('base_url', '') + endpoint
                            
                            step_result['request'] = {
                                'method': method,
                                'url': full_url,
                                'headers': request_config.get('headers', {}),
                                'body': request_config.get('body', {})
                            }
                            
                            # 执行请求
                            if step_type == 'polling':
                                success, response, error = runner.execute_polling(step)
                            elif step_type == 'repeat':
                                success, response, error = runner.execute_repeat(step)
                            else:
                                success, response, error = runner.execute_step(step)
                            
                            # 记录响应信息
                            if response:
                                step_result['response'] = {
                                    'status_code': response.get('status_code', 0),
                                    'body': response.get('data', response) if isinstance(response, dict) else response
                                }
                            
                            if not success:
                                step_result['status'] = 'FAIL'
                                step_result['error_message'] = str(error) if error else '步骤执行失败'
                                case_result['status'] = 'FAIL'
                                case_result['error_message'] = f"{step_name}: {error}"
                                case_result['steps'].append(step_result)
                                break
                                
                        except Exception as e:
                            step_result['status'] = 'FAIL'
                            step_result['error_message'] = str(e)
                            case_result['status'] = 'FAIL'
                            case_result['error_message'] = f"{step_name}: {str(e)}"
                            case_result['steps'].append(step_result)
                            break
                        
                        case_result['steps'].append(step_result)
                    
                except Exception as e:
                    case_result['status'] = 'FAIL'
                    case_result['error_message'] = str(e)
                    logger.error(f"用例执行异常: {case_id}, 错误: {e}")
                
                case_result['duration'] = time.time() - case_start
                
                if case_result['status'] == 'PASS':
                    passed_cases += 1
                    logger.info(f"用例通过: {case_id}")
                else:
                    failed_cases += 1
                    logger.warning(f"用例失败: {case_id} - {case_result['error_message']}")
                
                report_generator.add_case_result(case_result)
            
            execution_end = datetime.now()
            report_generator.set_time(execution_start, execution_end)
            
        finally:
            # 恢复工作目录
            os.chdir(original_cwd)
        
        pass_rate = (passed_cases / total_cases * 100) if total_cases > 0 else 0
        logger.info(f"测试完成: {passed_cases}/{total_cases} 通过，通过率: {pass_rate:.1f}%")

        # 5. 生成 HTML 报告并上传到 COS
        report_url = None
        report_html_path = os.path.join(temp_dir, f'report_{execution_id}.html')
        report_generator.save_to_file(report_html_path)
        
        # 上传 HTML 报告（单文件）
        report_cos_dir = f"webtest_api_test_reports/{test_case.project_id}/"
        report_filename = f"report_{execution_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        try:
            cos_res = cos_client.upload_file_to_cos_bucket(
                report_cos_dir,
                report_filename,
                report_html_path,
                content_type='text/html; charset=utf-8'
            )
            if cos_res and 'ETag' in cos_res:
                report_url = f"https://{cos_client.bucket}.cos.ap-guangzhou.myqcloud.com/{report_cos_dir}{report_filename}"
                logger.info(f"报告上传成功: {report_url}")
        except Exception as e:
            logger.error(f"上传报告失败: {e}")

        # 8. 更新执行记录
        execution.status = ApiTestExecutionModel.ExecutionStatus.SUCCESS if failed_cases == 0 else ApiTestExecutionModel.ExecutionStatus.FAILED
        execution.total_cases = total_cases
        execution.passed_cases = passed_cases
        execution.failed_cases = failed_cases
        execution.pass_rate = pass_rate
        execution.report_url = report_url
        execution.finished_at = timezone.now()
        execution.duration = int((execution.finished_at - execution.started_at).total_seconds())
        execution.save()

        # 更新测试用例统计
        test_case.last_execution_status = ApiTestCaseModel.ExecutionStatus.SUCCESS if failed_cases == 0 else ApiTestCaseModel.ExecutionStatus.FAILED
        test_case.last_execution_time = execution.finished_at
        test_case.total_executions = (test_case.total_executions or 0) + 1
        if failed_cases == 0:
            test_case.success_count = (test_case.success_count or 0) + 1
        test_case.save(update_fields=[
            'last_execution_status', 'last_execution_time',
            'total_executions', 'success_count'
        ])

        response['code'] = ErrorCode.SUCCESS
        response['message'] = f'执行完成: {passed_cases}/{total_cases} 通过'
        response['data'] = {
            'execution_id': execution_id,
            'status': execution.status,
            'total_cases': total_cases,
            'passed_cases': passed_cases,
            'failed_cases': failed_cases,
            'pass_rate': pass_rate,
            'report_url': report_url
        }

    except ApiTestExecutionModel.DoesNotExist:
        response['code'] = ErrorCode.PARAM_INVALID
        response['message'] = f'执行记录不存在: {execution_id}'
        response['status_code'] = 400

    except ApiTestCaseModel.DoesNotExist:
        response['code'] = ErrorCode.PARAM_INVALID
        response['message'] = '测试用例不存在或已删除'
        response['status_code'] = 400
        update_execution_to_failed(execution_id, response['message'])

    except ApiTestEnvironmentModel.DoesNotExist:
        response['code'] = ErrorCode.PARAM_INVALID
        response['message'] = '环境配置不存在或已删除'
        response['status_code'] = 400
        update_execution_to_failed(execution_id, response['message'])

    except Exception as e:
        response['code'] = ErrorCode.SERVER_ERROR
        response['message'] = f'执行失败: {str(e)}'
        response['status_code'] = 500
        update_execution_to_failed(execution_id, str(e))

        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)

    finally:
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

    return response


def update_execution_to_failed(execution_id: int, error_message: str):
    """更新执行记录为失败状态"""
    try:
        execution = ApiTestExecutionModel.objects.get(id=execution_id)
        execution.status = ApiTestExecutionModel.ExecutionStatus.FAILED
        execution.error_message = error_message
        execution.finished_at = timezone.now()
        if execution.started_at:
            execution.duration = int((execution.finished_at - execution.started_at).total_seconds())
        execution.save()
    except Exception:
        pass


@shared_task
def generate_api_test_case_task(interface_ids: list, project_id: int, user_id: int) -> dict:
    """
    AI 自动生成接口测试用例任务（预留）

    :param interface_ids: 接口 ID 列表
    :param project_id: 项目 ID
    :param user_id: 用户 ID
    :return: 执行结果（与 Service 层响应格式一致）
    """
    # 响应格式与 Service 层保持一致
    response = {
        "code": ErrorCode.ERROR,
        "message": "AI 生成接口测试用例功能暂未实现",
        "data": {},
        "status_code": 501
    }

    # TODO: 实现 AI 生成接口测试用例逻辑

    return response
