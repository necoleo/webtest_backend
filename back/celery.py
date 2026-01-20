# -*- coding: utf-8 -*-
"""
Celery 配置文件
用于配置异步任务队列，支持接口测试执行、需求解析等异步任务
"""
import os
from celery import Celery

# 设置 Django settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back.settings')

# 创建 Celery 应用
app = Celery('back')

# 从 Django settings 中读取 Celery 配置，所有配置项以 CELERY_ 开头
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现 tasks 目录下的任务模块
app.autodiscover_tasks(['tasks'])

# 定时任务配置（Celery Beat）
app.conf.beat_schedule = {
    # 每分钟检查接口测试定时任务
    'check-api-test-scheduled-tasks': {
        'task': 'tasks.schedule_tasks.ScheduleTaskService.checkScheduledTasks',
        'schedule': 60.0,
    },
}
