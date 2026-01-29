from django.db import models


class FunctionalTestCaseModel(models.Model):

    class ExecutionStatusChoices(models.IntegerChoices):
        NOT_EXECUTED = 0, "未执行"
        RUNNING = 1, "执行中"
        PASS = 2, "通过"
        FAIL = 3, "失败"

    class CaseSourceChoices(models.IntegerChoices):
        MANUAL = 0, "手动创建"
        AI_GENERATED = 1, "AI生成"
        IMPORTED = 2, "导入"

    class PriorityChoices(models.IntegerChoices):
        P0 = 0, "P0-最高"
        P1 = 1, "P1-高"
        P2 = 2, "P2-中"
        P3 = 3, "P3-低"

    # id
    id = models.AutoField(
        primary_key=True,
        db_column="id",
    )

    # 所属项目
    project_id = models.IntegerField(
        db_column="所属项目id",
    )

    # 用例标题
    case_title = models.CharField(
        max_length=255,
        db_comment="用例标题"
    )

    # 前置条件
    precondition = models.TextField(
        null=True,
        blank=True,
        db_comment="前置条件"
    )

    # 测试步骤
    test_steps = models.TextField(
        db_comment="测试步骤"
    )

    # 预期结果
    expected_result = models.TextField(
        db_comment="预期结果"
    )

    # 所属模块
    module = models.CharField(
        null=True,
        max_length=100,
        db_comment="所属模块"
    )

    # 优先级
    priority = models.SmallIntegerField(
        choices=PriorityChoices.choices,
        default=PriorityChoices.P0,
        db_comment="优先级，P0-最高，P1-高，P2-中，P3-低"
    )

    # 备注
    comment = models.TextField(
        null=True,
        blank=True,
        db_comment="备注"
    )

    # 来源
    case_source = models.SmallIntegerField(
        choices=CaseSourceChoices.choices,
        default=CaseSourceChoices.MANUAL,
        db_comment="用例来源，0-手动，1-AI生成，2-导入"
    )

    # 所属需求项id
    requirement_id = models.IntegerField(
        db_comment="所属需求id"
    )

    # 执行情况
    execution_status = models.SmallIntegerField(
        choices=ExecutionStatusChoices.choices,
        default=ExecutionStatusChoices.NOT_EXECUTED,
        db_comment="最后执行状态, 0-未执行，1-执行中，2-通过，3-失败"
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
        db_table = 'functional_test_case'
        verbose_name = "测试用例"
        verbose_name_plural = verbose_name
        ordering = ['priority', '-created_at']