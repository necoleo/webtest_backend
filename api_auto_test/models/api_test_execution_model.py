from django.db import models


class ApiTestExecutionModel(models.Model):
    """接口测试执行记录模型"""

    class ExecutionStatus(models.IntegerChoices):
        PENDING = 0, "待执行"
        RUNNING = 1, "执行中"
        SUCCESS = 2, "成功"
        FAILED = 3, "失败"

    class TriggerType(models.IntegerChoices):
        MANUAL = 0, "手动触发"
        SCHEDULED = 1, "定时触发"

    # id
    id = models.AutoField(
        primary_key=True,
        db_comment="id"
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

    # 执行状态
    status = models.SmallIntegerField(
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING,
        db_comment="执行状态: 0-待执行, 1-执行中, 2-成功, 3-失败"
    )

    # 触发类型
    trigger_type = models.SmallIntegerField(
        choices=TriggerType.choices,
        default=TriggerType.MANUAL,
        db_comment="触发类型: 0-手动触发, 1-定时触发"
    )

    # 关联定时任务id（定时触发时）
    scheduled_task_id = models.IntegerField(
        null=True,
        blank=True,
        db_comment="关联定时任务id"
    )

    # Celery任务id
    celery_task_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_comment="Celery任务id"
    )

    # 总用例数
    total_cases = models.IntegerField(
        null=True,
        blank=True,
        default=0,
        db_comment="总用例数"
    )

    # 通过用例数
    passed_cases = models.IntegerField(
        null=True,
        blank=True,
        default=0,
        db_comment="通过用例数"
    )

    # 失败用例数
    failed_cases = models.IntegerField(
        null=True,
        blank=True,
        default=0,
        db_comment="失败用例数"
    )

    # 通过率（百分比）
    pass_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        db_comment="通过率（百分比）"
    )

    # 测试报告COS访问URL
    report_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        db_comment="测试报告COS访问URL"
    )

    # 错误信息
    error_message = models.TextField(
        null=True,
        blank=True,
        db_comment="错误信息"
    )

    # 开始执行时间
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        db_comment="开始执行时间"
    )

    # 执行完成时间
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        db_comment="执行完成时间"
    )

    # 执行耗时（秒）
    duration = models.IntegerField(
        null=True,
        blank=True,
        db_comment="执行耗时（秒）"
    )

    # 执行人id
    executed_user_id = models.IntegerField(
        null=True,
        db_comment="执行人id"
    )

    # 执行人
    executed_user = models.CharField(
        max_length=255,
        null=True,
        db_comment="执行人"
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

    class Meta:
        db_table = 'api_test_execution'
        verbose_name = '接口测试执行记录'
        verbose_name_plural = '接口测试执行记录'
        ordering = ['-created_at']
