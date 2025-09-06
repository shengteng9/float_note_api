#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目初始化脚本 - 用于添加分类数据
"""

import os
import sys
import django
from datetime import datetime
from constants import default_categories

# 设置Django环境变量
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sovo.settings")
django.setup()

# 导入必要的模型
from accounts.models.user_model import User
from records.models.category_model import Category
from records.models.field_spec import FieldSpec


def init_categories_for_user(user_id):
    """
    为指定用户初始化分类数据
    :param user_id: 用户ID
    """
    try:
        # 获取用户对象
        user = User.objects.get(id=user_id)
        print(f"找到用户: {user.username}")

        # 添加分类数据
        for category_data in default_categories:
            # 检查分类是否已存在
            existing_category = Category.objects.filter(
                name=category_data["name"], user=user
            ).first()

            if existing_category:
                print(f"分类 '{category_data['name']}' 已存在，跳过...")
                continue

            # 创建FieldSpec对象列表
            field_specs = []
            for spec_data in category_data.pop("field_specs"):
                field_spec = FieldSpec(**spec_data)
                field_specs.append(field_spec)

            # 创建并保存Category对象
            category = Category(
                user=user,
                field_specs=field_specs,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **category_data,
            )
            category.save()
            print(f"成功创建分类: {category.name}")

        print("\n分类数据初始化完成！")

    except User.DoesNotExist:
        print(f"错误: 找不到ID为 '{user_id}' 的用户")
    except Exception as e:
        print(f"初始化过程中发生错误: {str(e)}")


if __name__ == "__main__":
    # 指定用户ID
    TARGET_USER_ID = "68a54e5cd0de154d029561d9"

    print(f"开始初始化用户 '{TARGET_USER_ID}' 的分类数据...")
    init_categories_for_user(TARGET_USER_ID)
