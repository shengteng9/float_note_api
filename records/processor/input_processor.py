import re
from sched import Event
from typing import List, Dict, Any
from ..models import RawInput, EventType, Category
from .text_processor import TextProcessor
from .image_processor import ImageProcessor
from .audio_processor import AudioProcessor



class InputProcessor:
    def __init__(self, raw_inputs: List[RawInput]):
        self.raw_inputs = raw_inputs
        self.processors = {
            'text': TextProcessor(),
            'image': ImageProcessor(),
            'audio': AudioProcessor()
        }
    
    def process(self) -> Dict[str, Any]:
        """处理所有输入并返回结构化数据"""
        all_content = {} # 所有输入的结构化数据
        detected_types = [] # 检测到的类型
        total_confidence = 0.0 # 所有输入的置信度
        input_count = len(self.raw_inputs) # 输入的数量
        
        for raw_input in self.raw_inputs:
            processor = self.processors.get(raw_input.type)
            if processor:
                result = processor.process(raw_input.content)
                all_content.update(result['content'])
                detected_types.append(result['type'])
                total_confidence += result['confidence']
        
        # 确定最终类型
        final_type = self._determine_type(detected_types)
        avg_confidence = total_confidence / input_count if input_count > 0 else 0.0
        
        return {
            'type': final_type,
            'content': all_content,
            'confidence': avg_confidence
        }
    
    def _determine_type(self, detected_types: List[str]) -> str:
        """根据检测到的类型确定最终类型"""
        if not detected_types:
            return EventType.UNKNOWN.value
        
        # 简单的类型优先级逻辑
        type_priority = {
            EventType.BILL.value: 5,
            EventType.SCHEDULE.value: 4,
            EventType.EXPENSE.value: 3,
            EventType.TASK.value: 2,
            EventType.CONTACT.value: 1,
            EventType.NOTE.value: 0
        }
        
        # 选择优先级最高的类型
        return max(detected_types, key=lambda x: type_priority.get(x, -1), default=EventType.UNKNOWN.value)