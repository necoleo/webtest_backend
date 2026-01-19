from django.db import models


class ApiTestCaseModel(models.Model):
    """接口测试用例模型"""

    class CaseSource(models.IntegerChoices):
        UPLOAD = 0, "上传"
        AI_GENERATED = 1, "AI生成"

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

    # 用例名称
    case_name = models.CharField(
        max_length=255,
        null=False,
        db_comment="用例名称"
    )

    # 用例描述
    description = models.TextField(
        null=True,
        blank=True,
        db_comment="用例描述"
    )

    # YAML文件COS访问URL
    cos_access_url = models.URLField(
        max_length=500,
        null=False,
        db_comment="YAML文件COS访问URL"
    )

    # 文件大小（字节）
    file_size = models.BigIntegerField(
        null=False,
        default=0,
        db_comment="文件大小（字节）"
    )

    # 用例来源
    source = models.SmallIntegerField(
        choices=CaseSource.choices,
        default=CaseSource.UPLOAD,
        db_comment="用例来源: 0-上传, 1-AI生成"
    )

    # AI生成时关联的接口ID列表（JSON格式）
    ai_source_interface_ids = models.JSONField(
        null=True,
        blank=True,
        db_comment="AI生成时关联的接口ID列表"
    )

    # 最后执行状态
    last_execution_status = models.SmallIntegerField(
        choices=ExecutionStatus.choices,
        null=True,
        blank=True,
        db_comment="最后执行状态: 0-待执行, 1-执行中, 2-成功, 3-失败"
    )

    # 最后执行时间
    last_execution_time = models.DateTimeField(
        null=True,
        blank=True,
        db_comment="最后执行时间"
    )

    # 总执行次数
    total_executions = models.IntegerField(
        null=False,
        default=0,
        db_comment="总执行次数"
    )

    # 成功执行次数
    success_count = models.IntegerField(
        null=False,
        default=0,
        db_comment="成功执行次数"
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
        db_table = 'api_test_case'
        verbose_name = '接口测试用例'
        verbose_name_plural = '接口测试用例'
        ordering = ['-created_at']
