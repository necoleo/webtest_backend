import re

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.
class User(AbstractUser):
    # 新增手机号码字段
    phone = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        verbose_name='手机号码',
        db_comment='手机号码'
    )


    # 校验逻辑
    def clean(self):
        # username 校验
        if len(self.username) < 3:
            raise ValidationError("用户名过短")
        if len(self.username) > 32:
            raise ValidationError("用户名过长")
        # 非字母和数字
        username_pattern = r'[^a-zA-Z0-9]'
        if re.match(username_pattern, self.username):
            raise ValidationError("存在非法字符")

        # password 校验
        if len(self.password) < 3:
            raise ValidationError("密码过短")
        if len(self.password) > 128:
            raise ValidationError("密码过长")

