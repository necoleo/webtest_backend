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

# Docker 环境中 api_auto_test 挂载在 /api_auto_test
# 本地开发环境中在项目根目录的 api_auto_test 下
if os.path.exists('/api_auto_test'):
    API_AUTO_TEST_DIR = '/api_auto_test'
else:
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


class ApiTestTaskService:
    """接口测试任务服务类"""

    @staticmethod
    @shared_task(bind=True, max_retries=3)
    def executeApiTestTask(task, executionId: int) -> dict:
        """
        执行接口测试任务（Celery 任务入口）

        流程：
        1. 从数据库获取执行记录和相关配置
        2. 从 COS 下载 YAML 测试用例文件
        3. 解析环境配置，覆盖 YAML 中的 config
        4. 使用 YAMLTestRunner 执行测试，收集每个步骤的详细请求/响应信息
        5. 生成自制 HTML 报告（单文件，包含所有 CSS/JS）
        6. 将报告上传到 COS
        7. 更新执行记录状态

        :param task: Celery 任务实例
        :param executionId: 执行记录 ID
        :return: 执行结果
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        tempDir = None

        try:
            # 1. 获取执行记录
            execution = ApiTestExecutionModel.objects.get(id=executionId)
            execution.status = ApiTestExecutionModel.ExecutionStatus.RUNNING
            execution.started_at = timezone.now()
            execution.save(update_fields=['status', 'started_at'])

            # 获取测试用例和环境配置
            testCase = ApiTestCaseModel.objects.get(id=execution.test_case_id, deleted_at__isnull=True)
            environment = ApiTestEnvironmentModel.objects.get(id=execution.env_id, deleted_at__isnull=True)

            # 2. 创建临时目录并从 COS 下载 YAML 文件
            tempDir = tempfile.mkdtemp(prefix='api_test_')
            cosClient = CosClient()

            # 下载 YAML 文件
            yamlFilename = os.path.basename(testCase.cos_access_url.split('?')[0])
            yamlPath = os.path.join(tempDir, yamlFilename)

            # 解析 COS Key
            cosKey = testCase.cos_access_url.split('.com/')[-1].split('?')[0]
            cosClient.client.download_file(
                Bucket=cosClient.bucket,
                Key=cosKey,
                DestFilePath=yamlPath
            )

            # 3. 加载 YAML 并覆盖环境配置
            with open(yamlPath, 'r', encoding='utf-8') as f:
                yamlData = yaml.safe_load(f)

            # 确保 config 存在
            if 'config' not in yamlData:
                yamlData['config'] = {}

            # 覆盖环境配置
            yamlData['config']['base_url'] = environment.base_url
            if environment.timeout:
                yamlData['config']['timeout'] = environment.timeout
            if environment.headers:
                yamlData['config']['headers'] = environment.headers

            # 合并环境变量到 config
            if environment.variables:
                for key, value in environment.variables.items():
                    yamlData['config'][key] = value

            # 保存修改后的 YAML
            with open(yamlPath, 'w', encoding='utf-8') as f:
                yaml.dump(yamlData, f, allow_unicode=True, default_flow_style=False)

            # 4. 直接使用 YAMLTestRunner 执行测试
            logger.info(f"开始执行测试，YAML 路径: {yamlPath}")

            from src.test_cases_parser import YAMLTestRunner  # type: ignore

            originalCwd = os.getcwd()
            os.chdir(API_AUTO_TEST_DIR)

            try:
                runner = YAMLTestRunner(yamlPath)
                cases = runner.get_cases()
                totalCases = len(cases)

                reportGenerator = HtmlReportGenerator()
                reportGenerator.set_test_info(
                    name=testCase.case_name,
                    environment=environment.env_name,
                    base_url=environment.base_url
                )

                executionStart = datetime.now()
                passedCases = 0
                failedCases = 0

                for case in cases:
                    caseId = case.get('case', 'UNKNOWN')
                    caseName = case.get('name', caseId)

                    logger.info(f"执行用例: {caseId} - {caseName}")

                    caseStart = time.time()
                    caseResult = {
                        'case_id': caseId,
                        'case_name': caseName,
                        'status': 'PASS',
                        'duration': 0,
                        'error_message': '',
                        'steps': []
                    }

                    try:
                        runner.var_handler = runner.var_handler.__class__(runner.config)

                        for step in case.get('steps', []):
                            stepName = step.get('name', 'unknown_step')
                            stepType = step.get('type', 'http_request')

                            stepResult = {
                                'name': stepName,
                                'status': 'PASS',
                                'error_message': '',
                                'request': {},
                                'response': {}
                            }

                            try:
                                requestConfig = runner.var_handler.replace_variables(step.get('request', {}))

                                method = requestConfig.get('method', 'GET')
                                endpoint = requestConfig.get('endpoint', '')
                                fullUrl = runner.config.get('base_url', '') + endpoint

                                stepResult['request'] = {
                                    'method': method,
                                    'url': fullUrl,
                                    'headers': requestConfig.get('headers', {}),
                                    'body': requestConfig.get('body', {})
                                }

                                if stepType == 'polling':
                                    success, stepResponse, error = runner.execute_polling(step)
                                elif stepType == 'repeat':
                                    success, stepResponse, error = runner.execute_repeat(step)
                                else:
                                    success, stepResponse, error = runner.execute_step(step)

                                # 无论成功失败都记录响应信息
                                if stepResponse:
                                    if isinstance(stepResponse, dict):
                                        stepResult['response'] = {
                                            'status_code': stepResponse.get('status_code', 0),
                                            'body': stepResponse.get('data', stepResponse)
                                        }
                                    else:
                                        stepResult['response'] = {
                                            'status_code': 0,
                                            'body': stepResponse
                                        }
                                else:
                                    stepResult['response'] = {
                                        'status_code': 0,
                                        'body': None,
                                        'error': str(error) if error else '无响应'
                                    }

                                if not success:
                                    stepResult['status'] = 'FAIL'
                                    stepResult['error_message'] = str(error) if error else '步骤执行失败'
                                    caseResult['status'] = 'FAIL'
                                    caseResult['error_message'] = f"{stepName}: {error}"
                                    caseResult['steps'].append(stepResult)
                                    break

                            except Exception as e:
                                stepResult['status'] = 'FAIL'
                                stepResult['error_message'] = str(e)
                                # 确保异常时也记录请求信息（如果还未记录）
                                if not stepResult['request']:
                                    rawRequest = step.get('request', {})
                                    stepResult['request'] = {
                                        'method': rawRequest.get('method', 'GET'),
                                        'url': runner.config.get('base_url', '') + rawRequest.get('endpoint', ''),
                                        'headers': rawRequest.get('headers', {}),
                                        'body': rawRequest.get('body', {})
                                    }
                                # 记录异常响应
                                stepResult['response'] = {
                                    'status_code': 0,
                                    'body': None,
                                    'error': str(e)
                                }
                                caseResult['status'] = 'FAIL'
                                caseResult['error_message'] = f"{stepName}: {str(e)}"
                                caseResult['steps'].append(stepResult)
                                break

                            caseResult['steps'].append(stepResult)

                    except Exception as e:
                        caseResult['status'] = 'FAIL'
                        caseResult['error_message'] = str(e)
                        logger.error(f"用例执行异常: {caseId}, 错误: {e}")

                    caseResult['duration'] = time.time() - caseStart

                    if caseResult['status'] == 'PASS':
                        passedCases += 1
                        logger.info(f"用例通过: {caseId}")
                    else:
                        failedCases += 1
                        logger.warning(f"用例失败: {caseId} - {caseResult['error_message']}")

                    reportGenerator.add_case_result(caseResult)

                executionEnd = datetime.now()
                reportGenerator.set_time(executionStart, executionEnd)

            finally:
                os.chdir(originalCwd)

            passRate = (passedCases / totalCases * 100) if totalCases > 0 else 0
            logger.info(f"测试完成: {passedCases}/{totalCases} 通过，通过率: {passRate:.1f}%")

            # 5. 生成 HTML 报告并上传到 COS
            reportUrl = None
            reportHtmlPath = os.path.join(tempDir, f'report_{executionId}.html')
            reportGenerator.save_to_file(reportHtmlPath)

            reportCosDir = f"webtest/webtest_api_test_reports/{testCase.project_id}/"
            reportFilename = f"report_{executionId}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.html"

            try:
                cosRes = cosClient.upload_file_to_cos_bucket(
                    reportCosDir,
                    reportFilename,
                    reportHtmlPath,
                    content_type='text/html; charset=utf-8'
                )
                if cosRes and 'ETag' in cosRes:
                    reportUrl = f"https://{cosClient.bucket}.cos.ap-guangzhou.myqcloud.com/{reportCosDir}{reportFilename}"
                    logger.info(f"报告上传成功: {reportUrl}")
            except Exception as e:
                logger.error(f"上传报告失败: {e}")

            # 6. 更新执行记录
            execution.status = ApiTestExecutionModel.ExecutionStatus.SUCCESS if failedCases == 0 else ApiTestExecutionModel.ExecutionStatus.FAILED
            execution.total_cases = totalCases
            execution.passed_cases = passedCases
            execution.failed_cases = failedCases
            execution.pass_rate = passRate
            execution.report_url = reportUrl
            execution.finished_at = timezone.now()
            execution.duration = int((execution.finished_at - execution.started_at).total_seconds())
            execution.save()

            # 更新测试用例统计
            testCase.last_execution_status = ApiTestCaseModel.ExecutionStatus.SUCCESS if failedCases == 0 else ApiTestCaseModel.ExecutionStatus.FAILED
            testCase.last_execution_time = execution.finished_at
            testCase.total_executions = (testCase.total_executions or 0) + 1
            if failedCases == 0:
                testCase.success_count = (testCase.success_count or 0) + 1
            testCase.save(update_fields=[
                'last_execution_status', 'last_execution_time',
                'total_executions', 'success_count'
            ])

            response['code'] = ErrorCode.SUCCESS
            response['message'] = f'执行完成: {passedCases}/{totalCases} 通过'
            response['data'] = {
                'execution_id': executionId,
                'status': execution.status,
                'total_cases': totalCases,
                'passed_cases': passedCases,
                'failed_cases': failedCases,
                'pass_rate': passRate,
                'report_url': reportUrl
            }

        except ApiTestExecutionModel.DoesNotExist:
            response['code'] = ErrorCode.PARAM_INVALID
            response['message'] = f'执行记录不存在: {executionId}'
            response['status_code'] = 400

        except ApiTestCaseModel.DoesNotExist:
            response['code'] = ErrorCode.PARAM_INVALID
            response['message'] = '测试用例不存在或已删除'
            response['status_code'] = 400
            ApiTestTaskService.updateExecutionToFailed(executionId, response['message'])

        except ApiTestEnvironmentModel.DoesNotExist:
            response['code'] = ErrorCode.PARAM_INVALID
            response['message'] = '环境配置不存在或已删除'
            response['status_code'] = 400
            ApiTestTaskService.updateExecutionToFailed(executionId, response['message'])

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = f'执行失败: {str(e)}'
            response['status_code'] = 500
            ApiTestTaskService.updateExecutionToFailed(executionId, str(e))

            if task and task.request.retries < task.max_retries:
                raise task.retry(exc=e, countdown=60)

        finally:
            if tempDir and os.path.exists(tempDir):
                shutil.rmtree(tempDir, ignore_errors=True)

        return response

    @staticmethod
    def updateExecutionToFailed(executionId: int, errorMessage: str):
        """更新执行记录为失败状态"""
        try:
            execution = ApiTestExecutionModel.objects.get(id=executionId)
            execution.status = ApiTestExecutionModel.ExecutionStatus.FAILED
            execution.error_message = errorMessage
            execution.finished_at = timezone.now()
            if execution.started_at:
                execution.duration = int((execution.finished_at - execution.started_at).total_seconds())
            execution.save()
        except Exception:
            pass

    @staticmethod
    @shared_task
    def generateApiTestCaseTask(interfaceIds: list, projectId: int, userId: int) -> dict:
        """
        AI 自动生成接口测试用例任务（Celery 任务入口）

        :param interfaceIds: 接口 ID 列表
        :param projectId: 项目 ID
        :param userId: 用户 ID
        :return: 执行结果
        """
        response = {
            "code": ErrorCode.ERROR,
            "message": "AI 生成接口测试用例功能暂未实现",
            "data": {},
            "status_code": 501
        }

        # TODO: 实现 AI 生成接口测试用例逻辑

        return response
