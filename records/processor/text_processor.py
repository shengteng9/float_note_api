import re
from typing import Dict, Any
from datetime import datetime
from ..models import EventType


class TextProcessor:
    def __init__(self):
        self.patterns = {
            EventType.BILL.value: [
                r"(消费|支付|账单|收款|金额|¥|￥|元|人民币|)",
                r"\d+\.?\d*(元|人民币|RMB|块)",
            ],
            EventType.SCHEDULE.value: [
                r"(会议|预约|安排|时间|地点|参加)",
                r"\d{1,2}月\d{1,2}日|\d{1,2}:\d{2}",
            ],
            EventType.CONTACT.value: [
                r"(电话|手机|邮箱|地址|联系人|先生|女士)",
                r"1[3-9]\d{9}|@\w+\.\w+",
            ],
            EventType.EXPENSE.value: [
                r"(开销|花费|支出|费用|报销)",
                r"\d+\.?\d*(元|人民币)",
            ],
        }

    def process(self, text: str) -> Dict[str, Any]:
        """处理文本输入"""
        detected_type = EventType.UNKNOWN.value
        # 为每个类型单独存储置信度，而非全局累加
        type_confidence = {rt: 0.0 for rt in self.patterns.keys()}
        content = {"raw_text": text}

        # 类型检测
        for record_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    type_confidence[record_type] += 0.3

        # 2. 选择置信度最高的类型
        max_conf = max(type_confidence.values())
        if max_conf > 0.0:
            detected_type = max(type_confidence, key=lambda k: type_confidence[k])
        confidence = min(max_conf, 1.0)

        
        # 具体类型解析
        if detected_type == EventType.BILL.value:
            content.update(self._parse_bill(text))
        elif detected_type == EventType.SCHEDULE.value:
            content.update(self._parse_schedule(text))
        elif detected_type == EventType.CONTACT.value:
            content.update(self._parse_contact(text))
        elif detected_type == EventType.EXPENSE.value:
            content.update(self._parse_expense(text))

        return {
            "type": detected_type,
            "content": content,
            "confidence": confidence,  # 确保最大置信度在0.0-1.0之间
        }

    def _parse_bill(self, text: str) -> Dict[str, Any]:
        """解析账单信息"""
        result = {}

        # 提取金额
        # amount_match = re.search(r'(\d+\.?\d*)(元|人民币|RMB|¥|￥)', text)
        amount_match = re.search(r"([¥￥])?(\d+\.?\d*)(元|人民币|RMB)?", text)
        if amount_match:
            result["amount"] = float(amount_match.group(2))
            result["currency"] = "CNY"

        # 提取商家
        merchant_match = re.search(r"(在|于|从)([\w\s]+)(消费|支付|购买)", text)
        if merchant_match:
            result["merchant"] = merchant_match.group(2).strip()

        # 提取日期
        date_match = re.search(r"(\d{4}年)?(\d{1,2}月\d{1,2}日)", text)
        if date_match:
            result["date"] = date_match.group(0)

        return result

    def _parse_schedule(self, text: str) -> Dict[str, Any]:
        """解析日程信息"""
        result = {}

        # 提取时间
        # time_match = re.search(r'(\d{1,2}月\d{1,2}日)?\s*(\d{1,2}:\d{2})', text)
        # 修改后的正则表达式，可匹配多种日期格式
        time_match = re.search(
            r"(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}月\d{1,2}日)?\s*(\d{1,2}:\d{2})",
            text,
        )

        if time_match:
            result["time"] = time_match.group(0)

        # 提取地点
        location_match = re.search(r"(在|到|地点)([\w\s]+)(开会|见面|举行)", text)
        if location_match:
            result["location"] = location_match.group(2).strip()

        # 提取事件
        event_match = re.search(r"(会议|约会|活动|讨论)(关于|内容)?([\w\s]+)", text)
        if event_match:
            result["event"] = event_match.group(3).strip()

        return result
