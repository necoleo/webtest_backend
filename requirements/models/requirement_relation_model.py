from django.db import models


class RequirementRelationModel(models.Model):

    # id
    id = models.AutoField(
        primary_key=True,
        db_column='id',
    )

    # 源需求id
    source_requirement_id = models.IntegerField(
        db_column='源需求id',
    )

    # 目标需求id
    target_requirement_id = models.IntegerField(
        db_column='目标需求id',
    )

    # 相似度
    similarity_score = models.FloatField(
        db_column='相似度分数（0-1）',
    )

    # 匹配方式
    match_method = models.CharField(
        max_length=20,
        db_column='匹配方式：vector/manual',
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
        db_table = 'requirement_relation'
        verbose_name = "关联需求"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']