from django.db import models



# Create your models here.
class Projects(models.Model):

    class Project_Status(models.IntegerChoices):
        NOT_STARTED = 0 , "未开始"
        RUNNING = 1 , "进行中"
        FINISHED = 2 , "完成"
        PAUSED = 3 , "暂停"
        TERMINATED = 4 , "终止"

    # id
    id = models.AutoField(
        primary_key=True,
        db_comment="id"
    )

    # 项目编码
    project_code = models.CharField(
        max_length=32,
        unique=True,
        null=False,
        db_comment="项目编码"
    )

    # 项目名称
    project_name = models.CharField(
        max_length=128,
        unique=True,
        null=False,
        db_comment="项目名称"
    )

    # 项目描述
    description = models.TextField(
        null=True,
        db_comment="项目描述"
    )

    # 项目类型
    project_type = models.CharField(
        max_length=128,
        null=False,
        db_comment="项目类型"
    )

    # 项目状态
    project_status = models.PositiveSmallIntegerField(
        choices=Project_Status.choices,
        default=Project_Status.NOT_STARTED,
        db_comment="项目状态"
    )

    # 项目开始日期
    start_date = models.DateField(
        null=True,
        db_comment="项目开始日期"
    )

    # 项目结束时间
    end_date = models.DateField(
        null=True,
        db_comment="项目结束时间"
    )

    # 创建时间
    created_at = models.DateField(
        auto_now_add=True,
        db_comment="创建时间"
    )

    # 更新时间
    updated_at = models.DateField(
        auto_now=True,
        db_comment="更新时间"
    )