from django.db import models


class RequirementDocumentModel(models.Model):

    class RequirementDocumentStatus(models.IntegerChoices):
        NOT_PARSED = 0, "未解析"
        PARSING = 1, "解析中"
        PARSED = 2, "已解析"
        PARSING_FAILED = 3, "解析失败"

    # id
    id = models.AutoField(
        primary_key=True,
        db_column="id",
    )

    # 所属项目
    project_id = models.IntegerField(
        db_column="所属项目",
    )

    # 文档名称
    doc_name = models.CharField(
        max_length=255,
        db_column="需求文档名称",
    )

    # 版本
    version = models.CharField(
        max_length=50,
        null=True,
        db_column="版本号",
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

    # 解析状态
    parse_status = models.SmallIntegerField(
        choices=RequirementDocumentStatus.choices,
        default=RequirementDocumentStatus.NOT_PARSED,
        db_comment="解析状态: 0-未解析, 1-解析中, 2-已解析, 3-解析失败"
    )

    # 解析出的需求项数量
    requirement_count = models.IntegerField(
        null=True,
        db_comment="解析出的需求项数量"
    )

    # 创建人id
    created_user_id = models.IntegerField(
        db_comment="创建人id"
    )

    # 创建人名称
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

