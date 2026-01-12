from django.db import models


class ProjectModel(models.Model):
    """
    项目表
    """
    # 项目状态选项
    class ProjectStatus(models.IntegerChoices):
        NOT_STARTED = 0, "未开始"
        IN_PROGRESS = 1, "进行中"
        COMPLETED = 2, "完成"
        PAUSED = 3, "暂停"
        TERMINATED = 4, "终止"

    # id
    id = models.AutoField(
        primary_key=True,
        db_comment="id"
    )

    # 项目名称
    project_name = models.CharField(
        max_length=128,
        null=False,
        unique=True,
        db_comment="项目名称"
    )

    # 项目描述
    description = models.TextField(
        null=True,
        db_comment="项目描述"
    )

    # 项目类型
    project_type = models.CharField(
        null=True,
        max_length=64,
        db_comment="项目类型"
    )

    # 项目状态，0-未开始、1-进行中、2-完成、3-暂停、4-终止
    project_status = models.SmallIntegerField(
        choices=ProjectStatus.choices,
        default=ProjectStatus.NOT_STARTED,
        db_comment="项目状态"
    )

    # 计划开始日期
    start_date = models.DateField(
        null=True,
        db_comment="计划开始日期"
    )

    # 计划结束日期
    end_date = models.DateField(
        null=True,
        db_comment="计划结束日期"
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