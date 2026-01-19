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
from tasks.api_test_tasks import execute_api_test_task
from constant.error_code import ErrorCode

logger = logging.getLogger(__name__)


@shared_task
def check_api_test_scheduled_tasks() -> dict:
    """
    检查接口测试定时任务

    每分钟执行一次，检查是否有到达执行时间的定时任务，触发执行。

    调度逻辑：
    - daily: 每天在指定时间执行
    - weekly: 每周在指定星期的指定时间执行

    :return: 执行结果（与 Service 层响应格式一致）
    """
    # 响应格式与 Service 层保持一致
    response = {
        "code": "",
        "message": "",
        "data": {},
        "status_code": 200
    }

    now = timezone.now()
    # 转换为本地时间进行比较（因为 schedule_time 是本地时间）
    local_now = timezone.localtime(now)
    current_time = local_now.time()
    current_weekday = local_now.isoweekday()  # 1=Monday, 7=Sunday

    # 查询所有启用的定时任务
    schedules = ApiTestScheduleModel.objects.filter(
        is_enabled=True,
        deleted_at__isnull=True
    )

    triggered_count = 0
    triggered_tasks = []
    errors = []

    for schedule in schedules:
        should_trigger = False

        # 检查是否应该触发
        if schedule.schedule_type == ApiTestScheduleModel.ScheduleType.DAILY:
            # 每天执行：检查当前时间是否在执行时间附近（同一分钟）
            schedule_hour = schedule.schedule_time.hour
            schedule_minute = schedule.schedule_time.minute
            current_hour = current_time.hour
            current_minute = current_time.minute

            # 简单比较：同一小时且同一分钟
            should_trigger = (schedule_hour == current_hour and schedule_minute == current_minute)

        elif schedule.schedule_type == ApiTestScheduleModel.ScheduleType.WEEKLY:
            # 每周执行：检查星期和时间
            if schedule.schedule_weekday == current_weekday:
                schedule_hour = schedule.schedule_time.hour
                schedule_minute = schedule.schedule_time.minute
                current_hour = current_time.hour
                current_minute = current_time.minute

                should_trigger = (schedule_hour == current_hour and schedule_minute == current_minute)

        # 检查是否已经在今天执行过（避免重复执行）
        if should_trigger and schedule.last_execution_time:
            last_exec_local = timezone.localtime(schedule.last_execution_time)
            if last_exec_local.date() == local_now.date():
                # 今天已经执行过
                if schedule.schedule_type == ApiTestScheduleModel.ScheduleType.DAILY:
                    # 每日任务：今天已执行，跳过
                    should_trigger = False
                elif schedule.schedule_type == ApiTestScheduleModel.ScheduleType.WEEKLY:
                    # 每周任务：本周同一天已执行，跳过
                    should_trigger = False

        if should_trigger:
            try:
                # 创建执行记录
                execution = ApiTestExecutionModel.objects.create(
                    test_case_id=schedule.test_case_id,
                    env_id=schedule.env_id,
                    status=ApiTestExecutionModel.ExecutionStatus.PENDING,
                    trigger_type=ApiTestExecutionModel.TriggerType.SCHEDULED,
                    scheduled_task_id=schedule.id,
                    executed_user_id=schedule.created_user_id,
                    executed_user=schedule.created_user
                )

                # 触发异步执行任务
                task = execute_api_test_task.delay(execution.id)

                # 更新执行记录的 Celery 任务 ID
                execution.celery_task_id = task.id
                execution.save(update_fields=['celery_task_id'])

                # 更新定时任务的执行信息
                schedule.last_execution_time = now
                schedule.last_execution_status = ApiTestScheduleModel.ExecutionStatus.PENDING

                # 计算下次执行时间
                if schedule.schedule_type == ApiTestScheduleModel.ScheduleType.DAILY:
                    # 下一天的同一时间
                    next_date = local_now.date() + timedelta(days=1)
                    next_time = timezone.make_aware(
                        datetime.combine(next_date, schedule.schedule_time)
                    )
                elif schedule.schedule_type == ApiTestScheduleModel.ScheduleType.WEEKLY:
                    # 下周同一天的同一时间
                    days_until_next = 7  # 下周同一天
                    next_date = local_now.date() + timedelta(days=days_until_next)
                    next_time = timezone.make_aware(
                        datetime.combine(next_date, schedule.schedule_time)
                    )
                else:
                    next_time = None

                schedule.next_execution_time = next_time
                schedule.save(update_fields=[
                    'last_execution_time', 'last_execution_status', 'next_execution_time'
                ])

                triggered_count += 1
                triggered_tasks.append({
                    'schedule_id': schedule.id,
                    'task_name': schedule.task_name,
                    'execution_id': execution.id,
                    'celery_task_id': task.id
                })

                logger.info(f"触发定时任务: {schedule.task_name} (schedule_id={schedule.id}, execution_id={execution.id})")

            except Exception as e:
                # 记录错误但不中断其他任务的检查
                error_msg = f"触发定时任务 {schedule.id} ({schedule.task_name}) 失败: {str(e)}"
                logger.error(error_msg)
                errors.append({
                    'schedule_id': schedule.id,
                    'task_name': schedule.task_name,
                    'error': str(e)
                })

    response['code'] = ErrorCode.SUCCESS
    response['message'] = f'检查完成，触发了 {triggered_count} 个定时任务'
    response['data'] = {
        'checked_at': now.isoformat(),
        'triggered_count': triggered_count,
        'triggered_tasks': triggered_tasks,
        'errors': errors
    }

    return response


@shared_task
def update_schedule_execution_status() -> dict:
    """
    更新定时任务的执行状态

    定期检查定时任务关联的最近执行记录，更新定时任务的 last_execution_status。

    :return: 执行结果
    """
    response = {
        "code": "",
        "message": "",
        "data": {},
        "status_code": 200
    }

    updated_count = 0

    try:
        # 获取所有有最近执行时间且状态为 PENDING 的定时任务
        schedules = ApiTestScheduleModel.objects.filter(
            is_enabled=True,
            deleted_at__isnull=True,
            last_execution_status=ApiTestScheduleModel.ExecutionStatus.PENDING,
            last_execution_time__isnull=False
        )

        for schedule in schedules:
            # 查询该定时任务最近的执行记录
            try:
                latest_execution = ApiTestExecutionModel.objects.filter(
                    scheduled_task_id=schedule.id
                ).order_by('-created_at').first()

                if latest_execution:
                    # 如果执行已完成，更新定时任务状态
                    if latest_execution.status in [
                        ApiTestExecutionModel.ExecutionStatus.SUCCESS,
                        ApiTestExecutionModel.ExecutionStatus.FAILED
                    ]:
                        if latest_execution.status == ApiTestExecutionModel.ExecutionStatus.SUCCESS:
                            schedule.last_execution_status = ApiTestScheduleModel.ExecutionStatus.SUCCESS
                        else:
                            schedule.last_execution_status = ApiTestScheduleModel.ExecutionStatus.FAILED

                        schedule.save(update_fields=['last_execution_status'])
                        updated_count += 1

            except Exception as e:
                logger.error(f"更新定时任务 {schedule.id} 状态失败: {str(e)}")

        response['code'] = ErrorCode.SUCCESS
        response['message'] = f'更新完成，共更新 {updated_count} 个定时任务状态'
        response['data'] = {
            'updated_count': updated_count
        }

    except Exception as e:
        response['code'] = ErrorCode.SERVER_ERROR
        response['message'] = f'更新失败: {str(e)}'
        response['status_code'] = 500
        logger.error(f"update_schedule_execution_status 失败: {str(e)}")

    return response
