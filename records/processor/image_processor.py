from sched import Event
from typing import Dict, Any
from rapidocr import RapidOCR
from PIL import Image
import io
import numpy as np
import cv2
import base64
from ..models import EventType

class ImageProcessor:
    def process(self, image_data: str) -> Dict[str, Any]:
        """处理图片输入"""
        ocr = RapidOCR()
        try:
            # 如果是base64编码的图片
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # 解码图片
            image_bytes = base64.b64decode(image_data)
            image_array = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            # OCR文字识别
            text = ocr(image)
            text = ''.join([item[1] for item in text])
            print('ocr text:',text)
            
            # 使用文本处理器继续处理
            from .text_processor import TextProcessor
            text_processor = TextProcessor()
            result = text_processor.process(text)
            
            # 添加图片信息
            result['content']['image_size'] = image.size
            result['content']['image_format'] = image.format
            
            return result
            
        except Exception as e:
            return {
                'type': EventType.UNKNOWN.value,
                'content': {'error': str(e), 'raw_image': image_data[:100] + '...'},
                'confidence': 0.0
            }