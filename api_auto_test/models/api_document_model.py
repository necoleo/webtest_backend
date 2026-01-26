from django.db import models

class ApiDocumentsModel(models.Model):

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

    # 文档名称
    doc_name = models.CharField(
        max_length=255,
        null=False,
        db_comment="文档名称"
    )

    # 版本号
    version = models.CharField(
        max_length=50,
        null=False,
        db_comment="版本号，格式如 1.0.0"
    )

    # cos访问url
    cos_access_url = models.URLField(
        null=True,
        db_comment="cos访问url"
    )

    # 文件大小
    file_size = models.BigIntegerField(
        null=False,
        db_comment="文件大小（字节）"
    )

    # 备注
    comment = models.TextField(
        null=True,
        db_comment="备注说明"
    )

    # 是否已解析
    is_parsed = models.BooleanField(
        default=False,
        db_comment="是否已解析"
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

    #  创建时间
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
        db_comment="删除时间"
    )

    class Meta:
        db_table = 'api_documents'
        verbose_name = '接口文档'
        verbose_name_plural = '接口文档'
        ordering = ['-created_at']