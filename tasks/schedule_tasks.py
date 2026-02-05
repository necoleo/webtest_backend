# -*- coding: utf-8 -*-
"""
定时任务调度相关任务
负责检查和触发定时执行的接口测试任务
"""
import os
import sys
import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.utils import timezone

# 添加项目根目录到 Python 路径
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from api_auto_test.models import ApiTestScheduleModel, ApiTestExecutionModel
from tasks.api_test_tasks import ApiTestTaskService
from constant.error_code import ErrorCode

logger = logging.getLogger(__name__)


@shared_task(name='tasks.schedule_tasks.check_scheduled_tasks')
def check_scheduled_tasks() -> dict:
        """
        检查接口测试定时任务（Celery 任务入口）

        每分钟执行一次，检查是否有到达执行时间的定时任务，触发执行。

        调度逻辑：
        - daily: 每天在指定时间执行
        - weekly: 每周在指定星期的指定时间执行

        :return: 执行结果
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        now = timezone.now()
        localNow = timezone.localtime(now)
        currentTime = localNow.time()
        currentWeekday = localNow.isoweekday()

        schedules = ApiTestScheduleModel.objects.filter(
            is_enabled=True,
            deleted_at__isnull=True
        )

        triggeredCount = 0
        triggeredTasks = []
        errors = []

        for schedule in schedules:
            shouldTrigger = False

            if schedule.schedule_type == ApiTestScheduleModel.ScheduleType.DAILY:
                scheduleHour = schedule.schedule_time.hour
                scheduleMinute = schedule.schedule_time.minute
                currentHour = currentTime.hour
                currentMinute = currentTime.minute

                shouldTrigger = (scheduleHour == currentHour and scheduleMinute == currentMinute)

            elif schedule.schedule_type == ApiTestScheduleModel.ScheduleType.WEEKLY:
                if schedule.schedule_weekday == currentWeekday:
                    scheduleHour = schedule.schedule_time.hour
                    scheduleMinute = schedule.schedule_time.minute
                    currentHour = currentTime.hour
                    currentMinute = currentTime.minute

                    shouldTrigger = (scheduleHour == currentHour and scheduleMinute == currentMinute)

            if shouldTrigger and schedule.last_execution_time:
                lastExecLocal = timezone.localtime(schedule.last_execution_time)
                if lastExecLocal.date() == localNow.date():
                    if schedule.schedule_type == ApiTestScheduleModel.ScheduleType.DAILY:
                        shouldTrigger = False
                    elif schedule.schedule_type == ApiTestScheduleModel.ScheduleType.WEEKLY:
                        shouldTrigger = False

            if shouldTrigger:
                try:
                    execution = ApiTestExecutionModel.objects.create(
                        test_case_id=schedule.test_case_id,
                        env_id=schedule.env_id,
                        status=ApiTestExecutionModel.ExecutionStatus.PENDING,
                        trigger_type=ApiTestExecutionModel.TriggerType.SCHEDULED,
                        scheduled_task_id=schedule.id,
                        executed_user_id=schedule.created_user_id,
                        executed_user=schedule.created_user
                    )

                    task = ApiTestTaskService.executeApiTestTask.delay(execution.id)

                    execution.celery_task_id = task.id
                    execution.save(update_fields=['celery_task_id'])

                    schedule.last_execution_time = now
                    schedule.last_execution_status = ApiTestScheduleModel.ExecutionStatus.PENDING

                    nextTime = ScheduleTaskService.calculateNextExecutionTime(schedule, localNow)
                    schedule.next_execution_time = nextTime
                    schedule.save(update_fields=[
                        'last_execution_time', 'last_execution_status', 'next_execution_time'
                    ])

                    triggeredCount += 1
                    triggeredTasks.append({
                        'schedule_id': schedule.id,
                        'task_name': schedule.task_name,
                        'execution_id': execution.id,
                        'celery_task_id': task.id
                    })

                    logger.info(f"触发定时任务: {schedule.task_name} (schedule_id={schedule.id}, execution_id={execution.id})")

                except Exception as e:
                    errorMsg = f"触发定时任务 {schedule.id} ({schedule.task_name}) 失败: {str(e)}"
                    logger.error(errorMsg)
                    errors.append({
                        'schedule_id': schedule.id,
                        'task_name': schedule.task_name,
                        'error': str(e)
                    })

        response['code'] = ErrorCode.SUCCESS
        response['message'] = f'检查完成，触发了 {triggeredCount} 个定时任务'
        response['data'] = {
            'checked_at': now.isoformat(),
            'triggered_count': triggeredCount,
            'triggered_tasks': triggeredTasks,
            'errors': errors
        }

        return response

    @staticmethod
    def calculateNextExecutionTime(schedule, localNow):
        """计算下次执行时间"""
        if schedule.schedule_type == ApiTestScheduleModel.ScheduleType.DAILY:
            nextDate = localNow.date() + timedelta(days=1)
            nextTime = timezone.make_aware(
                datetime.combine(nextDate, schedule.schedule_time)
            )
        elif schedule.schedule_type == ApiTestScheduleModel.ScheduleType.WEEKLY:
            daysUntilNext = 7
            nextDate = localNow.date() + timedelta(days=daysUntilNext)
            nextTime = timezone.make_aware(
                datetime.combine(nextDate, schedule.schedule_time)
            )
        else:
            nextTime = None

        return nextTime

    @staticmethod
    @shared_task
    def updateExecutionStatus() -> dict:
        """
        更新定时任务的执行状态（Celery 任务入口）

        定期检查定时任务关联的最近执行记录，更新定时任务的 last_execution_status。

        :return: 执行结果
        """
        response = {
            "code": "",
            "message": "",
            "data": {},
            "status_code": 200
        }

        updatedCount = 0

        try:
            schedules = ApiTestScheduleModel.objects.filter(
                is_enabled=True,
                deleted_at__isnull=True,
                last_execution_status=ApiTestScheduleModel.ExecutionStatus.PENDING,
                last_execution_time__isnull=False
            )

            for schedule in schedules:
                try:
                    latestExecution = ApiTestExecutionModel.objects.filter(
                        scheduled_task_id=schedule.id
                    ).order_by('-created_at').first()

                    if latestExecution:
                        if latestExecution.status in [
                            ApiTestExecutionModel.ExecutionStatus.SUCCESS,
                            ApiTestExecutionModel.ExecutionStatus.FAILED
                        ]:
                            if latestExecution.status == ApiTestExecutionModel.ExecutionStatus.SUCCESS:
                                schedule.last_execution_status = ApiTestScheduleModel.ExecutionStatus.SUCCESS
                            else:
                                schedule.last_execution_status = ApiTestScheduleModel.ExecutionStatus.FAILED

                            schedule.save(update_fields=['last_execution_status'])
                            updatedCount += 1

                except Exception as e:
                    logger.error(f"更新定时任务 {schedule.id} 状态失败: {str(e)}")

            response['code'] = ErrorCode.SUCCESS
            response['message'] = f'更新完成，共更新 {updatedCount} 个定时任务状态'
            response['data'] = {
                'updated_count': updatedCount
            }

        except Exception as e:
            response['code'] = ErrorCode.SERVER_ERROR
            response['message'] = f'更新失败: {str(e)}'
            response['status_code'] = 500
            logger.error(f"updateExecutionStatus 失败: {str(e)}")

        return response
