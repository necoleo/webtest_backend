from django.db import models


class RequirementModel(models.Model):

    class RequirementStatus(models.IntegerChoices):
        PENDING = 0, "待审核"
        CONFIRMED = 1, "已审核"
        GENERATING = 2, "测试用例生成中"
        COVERED = 3, "测试用例已覆盖"
        DEPRECATED = 4, "已废弃"

    # id
    id = models.AutoField(
        primary_key=True,
        db_column='id',
    )

    # 所属项目id
    project_id = models.IntegerField(
        db_column='所属项目id',
    )

    # 所属需求文档id
    requirement_document_id = models.IntegerField(
        db_column='所属需求文档id',
    )

    # 需求标题
    requirement_title = models.CharField(
        null=True,
        max_length=255,
        db_comment="需求标题"
    )

    # 需求内容
    requirement_content = models.TextField(
        db_column='需求内容',
    )

    # 所属模块
    module = models.CharField(
        null=True,
        max_length=100,
        db_comment="所属模块"
    )

    # 状态
    status = models.SmallIntegerField(
        choices=RequirementStatus.choices,
        default=RequirementStatus.PENDING,
        db_comment="需求状态: 0-待审核，1-已审核，2-测试用例生成中，3-测试用例已覆盖，4-已废弃"
    )

    # 向量索引
    vector_index = models.IntegerField(
        null=True,
        db_column='FAISS向量索引',
    )

    # 是否已向量化
    is_vectorized = models.BooleanField(
        default=False,
        db_column='是否已向量化',
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

    class Meta:
        db_table = 'requirement'
        verbose_name = "需求项"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']