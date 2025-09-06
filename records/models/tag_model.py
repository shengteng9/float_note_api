from mongoengine import Document, EmbeddedDocument, fields
import datetime

class Tag(Document):
    name = fields.StringField(max_length=20, required=True, help_text='标签名称')
    created_at = fields.DateTimeField(default=datetime.datetime.now, help_text='创建时间')
    updated_at = fields.DateTimeField(default=datetime.datetime.now, help_text='更新时间')
    category = fields.ReferenceField('Category',  required=True, help_text='分类')
    user= fields.ReferenceField('User', required=True, help_text='关联用户')
    description = fields.StringField(default='', max_length=100, help_text='标签描述')
    system_created = fields.BooleanField(default=False, help_text='是否为系统创建标签')
    meta = {
        'collection': 'tags',
        'indexes': [
            'name',
            'category',
            'description',
            {'fields': ['user', 'name'], 'unique': True}
        ]
    }
