from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime

class FieldSpec(EmbeddedDocument):
    name = fields.StringField(required=True, help_text="分类的动态字段")
    field_type = fields.StringField(choices=[
        'string', 'number', 'boolean', 'date', 'array', 'reference'
    ], default='string', help_text="设置动态分类的类型")
    required = fields.BooleanField(default=False, help_text='该动态字段是否必填')
    default = fields.DynamicField(null=True, help_text="默认值")
    ref_model = fields.StringField(null=True, help_text="引用的model")
    description = fields.StringField(null=True, help_text="动态字段的描述")
    enum_values = fields.ListField(fields.StringField(), null=True, help_text="枚举值")
