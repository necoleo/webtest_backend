from django.db import models


class ApiTestEnvironmentModel(models.Model):
    """接口测试环境配置模型"""

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

    # 环境名称
    env_name = models.CharField(
        max_length=100,
        null=False,
        db_comment="环境名称，如：开发环境、测试环境、生产环境"
    )

    # 环境描述
    description = models.TextField(
        null=True,
        blank=True,
        db_comment="环境描述"
    )

    # 基础URL
    base_url = models.URLField(
        max_length=500,
        null=False,
        db_comment="基础URL，如：https://api.example.com"
    )

    # 请求超时时间（秒）
    timeout = models.IntegerField(
        null=True,
        blank=True,
        default=30,
        db_comment="请求超时时间（秒）"
    )

    # 公共请求头（JSON格式）
    headers = models.JSONField(
        null=True,
        blank=True,
        db_comment="公共请求头，JSON格式"
    )

    # 环境变量（JSON格式）
    variables = models.JSONField(
        null=True,
        blank=True,
        db_comment="环境变量，JSON格式，如：{\"token\": \"xxx\", \"user_id\": 123}"
    )

    # 是否为默认环境
    is_default = models.BooleanField(
        null=False,
        default=False,
        db_comment="是否为默认环境"
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
        db_table = 'api_test_environment'
        verbose_name = '接口测试环境配置'
        verbose_name_plural = '接口测试环境配置'
        ordering = ['-created_at']
