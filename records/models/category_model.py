
from mongoengine import Document, EmbeddedDocument, fields
import datetime
from enum import Enum
from .field_spec import FieldSpec

class Category(Document):
    name = fields.StringField(required=True, help_text='分类名称')
    description = fields.StringField(default='', max_length=300, help_text='分类描述')
    created_at = fields.DateTimeField(default=datetime.datetime.now, help_text='创建时间')
    updated_at = fields.DateTimeField(default=datetime.datetime.now, help_text='更新时间')
    user = fields.ReferenceField('User', help_text='用户')
    field_specs = fields.ListField(fields.EmbeddedDocumentField(FieldSpec), help_text='动态字段')
    is_default = fields.BooleanField(default=False, help_text="是否为系统自带分类")
    is_active = fields.BooleanField(default=True, help_text='是否被激活')
    
    meta = {
        'collection': 'categories',
        'indexes': [
            'name',
            'user'
        ]
    }
