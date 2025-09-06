"""
暂时保留
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import date, time

class RecordType(str, Enum):
    BILL = "bill"
    SCHEDULE = "schedule"
    CONTACT = "contact"
    NOTE = "note"
    TASK = "task"
    EXPENSE = "expense"

class BaseRecordSchema(BaseModel):
    type: RecordType
    # confidence: float = Field(ge=0.0, le=1.0, description="解析置信度")
    raw_text: str = Field(description="原始文本内容")

class BillSchema(BaseRecordSchema):
    type: RecordType = RecordType.BILL
    amount: float = Field(description="金额")
    currency: str = Field(default="CNY", description="货币类型")
    merchant: Optional[str] = Field(None, description="商家名称")
    category: Optional[str] = Field(None, description="消费类别")
    date: Optional[str] = Field(None, description="日期")
    time: Optional[str] = Field(None, description="时间")

class ScheduleSchema(BaseRecordSchema):
    type: RecordType = RecordType.SCHEDULE
    event: str = Field(description="事件名称")
    date: Optional[str] = Field(None, description="日期")
    time: Optional[str] = Field(None, description="时间")
    location: Optional[str] = Field(None, description="地点")
    participants: Optional[List[str]] = Field(None, description="参与人")

class ContactSchema(BaseRecordSchema):
    type: RecordType = RecordType.CONTACT
    name: str = Field(description="姓名")
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    company: Optional[str] = Field(None, description="公司")
    position: Optional[str] = Field(None, description="职位")

class ExpenseSchema(BaseRecordSchema):
    type: RecordType = RecordType.EXPENSE
    amount: float = Field(description="金额")
    category: str = Field(description="支出类别")
    description: Optional[str] = Field(None, description="描述")
    date: Optional[str] = Field(None, description="日期")

class TaskSchema(BaseRecordSchema):
    type: RecordType = RecordType.TASK
    title: str = Field(description="任务标题")
    priority: Optional[str] = Field(None, description="优先级")
    due_date: Optional[str] = Field(None, description="截止日期")
    status: Optional[str] = Field(default="pending", description="状态")

class NoteSchema(BaseRecordSchema):
    type: RecordType = RecordType.NOTE
    content: str = Field(description="笔记内容")
    tags: Optional[List[str]] = Field(None, description="标签")

# 类型映射
SCHEMA_MAPPING = {
    RecordType.BILL: BillSchema,
    RecordType.SCHEDULE: ScheduleSchema,
    RecordType.CONTACT: ContactSchema,
    RecordType.EXPENSE: ExpenseSchema,
    RecordType.TASK: TaskSchema,
    RecordType.NOTE: NoteSchema,
}