from django.db import models


class ApiTestScheduleModel(models.Model):
    """接口测试定时任务模型"""

    class ScheduleType(models.IntegerChoices):
        DAILY = 0, "每天"
        WEEKLY = 1, "每周"

    class ExecutionStatus(models.IntegerChoices):
        PENDING = 0, "待执行"
        RUNNING = 1, "执行中"
        SUCCESS = 2, "成功"
        FAILED = 3, "失败"

    # id
    id = models.AutoField(
        primary_key=True,
        db_comment="id"
    )

    # 所属项目id
    project_id = models.IntegerField(
        null=False,
        db_comment="所属项目id"
    )

    # 任务名称
    task_name = models.CharField(
        max_length=255,
        null=False,
        db_comment="任务名称"
    )

    # 任务描述
    description = models.TextField(
        null=True,
        blank=True,
        db_comment="任务描述"
    )

    # 关联测试用例id
    test_case_id = models.IntegerField(
        null=False,
        db_comment="关联测试用例id"
    )

    # 关联环境配置id
    env_id = models.IntegerField(
        null=False,
        db_comment="关联环境配置id"
    )

    # 调度类型
    schedule_type = models.SmallIntegerField(
        choices=ScheduleType.choices,
        default=ScheduleType.DAILY,
        db_comment="调度类型: 0-每天, 1-每周"
    )

    # 执行时间（时:分）
    schedule_time = models.TimeField(
        null=False,
        db_comment="执行时间"
    )

    # 执行星期（1-7，周一到周日，仅weekly类型使用）
    schedule_weekday = models.IntegerField(
        null=True,
        blank=True,
        db_comment="执行星期（1-7，周一到周日）"
    )

    # 是否启用
    is_enabled = models.BooleanField(
        null=False,
        default=True,
        db_comment="是否启用"
    )

    # 上次执行时间
    last_execution_time = models.DateTimeField(
        null=True,
        blank=True,
        db_comment="上次执行时间"
    )

    # 上次执行状态
    last_execution_status = models.SmallIntegerField(
        choices=ExecutionStatus.choices,
        null=True,
        blank=True,
        db_comment="上次执行状态: 0-待执行, 1-执行中, 2-成功, 3-失败"
    )

    # 下次执行时间
    next_execution_time = models.DateTimeField(
        null=True,
        blank=True,
        db_comment="下次执行时间"
    )

    # 创建人id
    created_user_id = models.IntegerField(
        null=True,
        db_comment="创建人id"
    )

    # 创建人
    created_user = models.CharField(
        max_length=255,
        null=True,
        db_comment="创建人"
    )

    # 创建时间
    created_at = models.DateTimeField(
        null=False,
        auto_now_add=True,
        db_comment="创建时间"
    )

    # 更新时间
    updated_at = models.DateTimeField(
        null=False,
        auto_now=True,
        db_comment="更新时间"
    )

    # 删除时间
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_comment="删除时间"
    )

    class Meta:
        db_table = 'api_test_schedule'
        verbose_name = '接口测试定时任务'
        verbose_name_plural = '接口测试定时任务'
        ordering = ['-created_at']
