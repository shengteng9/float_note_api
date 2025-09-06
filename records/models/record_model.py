from email.policy import default
from mongoengine import Document, EmbeddedDocument, fields
import datetime
from enum import Enum


class InputType(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"  # 暂时不支持Document


class RecordType(Enum):
    BILL = "bill"
    SCHEDULE = "schedule"
    CONTACT = "contact"
    NOTE = "note"
    TASK = "task"
    EXPENSE = "expense"
    UNKNOWN = "unknown"


class RawInput(EmbeddedDocument):
    type = fields.StringField(choices=[it.value for it in InputType], required=True)
    content = fields.StringField(required=False)
    file_path = fields.StringField(null=False)
    file_size = fields.IntField(null=False)
    uploaded_at = fields.DateTimeField(default=datetime.datetime.now)


class Record(Document):
    user = fields.ReferenceField("User", required=True)
    title = fields.StringField(
        required=False, help_text="后台、测试时使用，区分用户数据"
    )
    category = fields.ReferenceField("Category", default=None, help_text="分类")
    type = fields.StringField(default="", help_text="记录类型,从分类中获取")
    raw_inputs = fields.ListField(fields.EmbeddedDocumentField(RawInput))
    content = fields.DictField(default={})
    is_processed = fields.BooleanField(default=False)
    processed_at = fields.DateTimeField(null=True)
    created_at = fields.DateTimeField(default=datetime.datetime.now)
    updated_at = fields.DateTimeField(default=datetime.datetime.now)
    file_data = fields.DictField(required=False, default=None)

    meta = {
        "collection": "records",
        "indexes": ["user", "type", "is_processed", "category"],
    }

    def clean(self):
        if self.raw_inputs and not self.is_processed:
            self._auto_process()
        super(Record, self).clean()

    def _auto_process(self):
        """使用LLM处理器替代原来的规则处理器"""
        from ..llm_processor import LLMProcessor

        try:
            processor = LLMProcessor()
            result = processor.process_inputs(self.raw_inputs)

            self.type = result["type"]
            self.content = result["content"]
            self.is_processed = True
            self.processed_at = datetime.datetime.now()

        except Exception as e:
            # 处理失败时设置默认值
            self.type = RecordType.UNKNOWN.value
            self.content = {"error": str(e), "raw_inputs": len(self.raw_inputs)}
            # self.confidence = 0.0
            self.is_processed = True
            self.processed_at = datetime.datetime.now()
