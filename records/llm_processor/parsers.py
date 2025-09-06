import re
import json
from typing import Dict, Any, Optional
from langchain.output_parsers import PydanticOutputParser
from .schemas import SCHEMA_MAPPING, RecordType, BaseRecordSchema

class MultiTypeOutputParser:
    """多类型输出解析器"""
    
    def __init__(self):
        self.parsers = {
            record_type: PydanticOutputParser(pydantic_object=schema)
            for record_type, schema in SCHEMA_MAPPING.items()
        }
    
    def parse_output(self, record_type: RecordType, text: str) -> Dict[str, Any]:
        """解析特定类型的输出"""
        if record_type not in self.parsers:
            raise ValueError(f"Unsupported record type: {record_type}")
        
        try:
            parsed = self.parsers[record_type].parse(text)
            return parsed.dict()
        except Exception as e:
            # 尝试从JSON中提取
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """备用的JSON解析方法"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"error": "Failed to parse output", "raw_output": text}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON output", "raw_output": text}

class TypeDetector:
    """类型检测器"""
    
    TYPE_KEYWORDS = {
        RecordType.BILL: ["消费", "支付", "账单", "金额", "元", "¥", "￥"],
        RecordType.SCHEDULE: ["会议", "预约", "时间", "地点", "参加", "安排"],
        RecordType.CONTACT: ["电话", "手机", "邮箱", "地址", "联系人"],
        RecordType.EXPENSE: ["开销", "花费", "支出", "费用", "报销"],
        RecordType.TASK: ["任务", "待办", "完成", "截止", "优先级"],
        RecordType.NOTE: ["笔记", "记录", "想法", "备注", "提醒"]
    }
    
    def detect_type(self, text: str) -> RecordType:
        """基于关键词进行初步类型检测"""
        text_lower = text.lower()
        
        for record_type, keywords in self.TYPE_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return record_type
        
        return RecordType.NOTE  # 默认类型