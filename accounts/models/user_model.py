from mongoengine import Document, EmbeddedDocument, fields
from django.utils import timezone  # 正确导入 Django 的时区工具
from django.contrib.auth.hashers import make_password, check_password

class MemberShip(EmbeddedDocument):
    is_active = fields.BooleanField(default=False)
    type = fields.StringField(choices=('月度', '年度', '终身'))  # 中文选项
    start_date = fields.DateTimeField()
    end_date = fields.DateTimeField()
    auto_renew = fields.BooleanField(default=True)
    last_payment_id = fields.StringField()

class SubscriptionHistory(EmbeddedDocument):
    subscription_id = fields.StringField(required=True)
    start_date = fields.DateTimeField()
    end_date = fields.DateTimeField()
    payment_amount = fields.FloatField()
    currency = fields.StringField(default='CNY')  # 改为人民币
    payment_date = fields.DateTimeField()

class User(Document):
    username = fields.StringField(required=True, unique=True)
    password = fields.StringField(required=True)
    created_at = fields.DateTimeField(default=timezone.now)  # 注意这里没有括号
    updated_at = fields.DateTimeField(default=timezone.now)
    member_ship = fields.EmbeddedDocumentField(MemberShip, required=False, default=None)
    history = fields.ListField(fields.EmbeddedDocumentField(SubscriptionHistory), default=list)
    refresh_token = fields.StringField()
    
    meta = {
        'collection': 'users',
        'indexes': [
            'username',
            {'fields': ['member_ship.end_date'], 'expireAfterSeconds': 0}
        ]
    }

    # 添加is_authenticated属性，用于Django REST Framework权限检查
    # 根据Django认证规范，已认证用户的is_authenticated应返回True
    @property
    def is_authenticated(self):
        return True
    
    # 添加is_active属性，默认为True
    @property
    def is_active(self):
        return True

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super(User, self).save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username