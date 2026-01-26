from django.db import models


class ApiInterfaceModel(models.Model):

    # id
    id = models.AutoField(
        primary_key=True,
        db_column="id",
    )

    # 所属接口文档
    document_id = models.IntegerField(
        null=False,
        db_column="所属文档"
    )

    # 接口标题
    api_title = models.CharField(
        max_length=255,
        null=False,
        db_comment="接口标题"
    )

    # 接口url
    api_url = models.CharField(
        max_length=512,
        null=False,
        db_comment="接口URL路径"
    )

    # 请求方法
    method = models.CharField(
        max_length=20,
        null=False,
        db_comment="请求方法"
    )

    # 请求参数
    params = models.JSONField(
        null=True,
        db_comment="请求参数"
    )

    # 请求示例
    request_example = models.TextField(
        null=True,
        db_comment="请求示例"
    )

    # 响应示例
    response_example = models.TextField(
        null=True,
        db_comment="响应示例"
    )

    # 接口说明
    comment = models.TextField(
        null=True,
        db_comment="接口说明"
    )

    # 接口状态 (active/deprecated/archived)
    status = models.CharField(
        max_length=20,
        null=True,
        db_comment="状态"
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=False,
        db_comment="创建时间"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=False,
        db_comment="更新时间"
    )

    deleted_at = models.DateTimeField(
        null=True,
        db_comment="删除时间"
    )

    class Meta:
        db_table = 'api_interfaces'
        verbose_name = "接口信息"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
