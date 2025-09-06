
import os
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from rapidocr import RapidOCR
from faster_whisper import WhisperModel
from sovo.settings import BASE_DIR
from common.utils.exception_handler import CustomException, ErrorCode
from rest_framework import status
from opencc import OpenCC # 转简体
from common.ml_models.load_local_model import load_local_model


class MultiModalPreprocessor:
    """多模态预处理器"""

    def __init__(self):
       
        self.rapid_ocr = RapidOCR()
        self.whisper_model = WhisperModel(load_local_model('faster-whisper-small').load_model(), device="cpu", compute_type="int8")
        # 转换为简体中文
        self.cc = OpenCC('t2s')

    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_text_from_image(self, file_path: str) -> Optional[str]:
        """从图片中提取文本（使用OCR API）"""
        import time
        try:
            # 确保文件路径正确
            if not os.path.isabs(file_path):
                # 如果不是绝对路径，则从media/uploads目录构建完整路径
                full_path = os.path.join(BASE_DIR, 'media', 'uploads', file_path)
            else:
                full_path = file_path
            
            if not os.path.exists(full_path):
                print(f"文件不存在: {full_path}")
                return None

            with open(full_path, 'rb') as f:
                image_data = f.read()
            
            result = self.rapid_ocr(image_data)
            all_texts = '这是图片ocr识别出的内容(最好先清理数据（去除干扰字符、纠正明显错误），再进行其他操作。):'
            if result:
                if hasattr(result, 'txts') and result.txts:
                    # 如果有texts属性，使用它
                    all_texts += '|'.join(result.txts)
                else:
                    # 作为后备方案，尝试将结果转换为字符串
                    all_texts += f"这是图片ocr识别出的内容:{str(result)}"

                return all_texts
            return ""
            
        except Exception as e:
            print(f"OCR处理失败: {e}")
            raise CustomException(
                error_code=ErrorCode.UNKNOWN_ERROR,
                error_message=f"OCR处理失败: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_text_from_audio(self, file_path: str) -> Optional[str]:
        """从音频中提取文本（使用Whisper API）"""
        try:
            # 确保文件路径正确
            if not os.path.isabs(file_path):
                # 如果不是绝对路径，则从media/uploads目录构建完整路径
                full_path = os.path.join(BASE_DIR, 'media', 'uploads', file_path)
            else:
                full_path = file_path
            
            # 检查文件是否存在
            if not os.path.exists(full_path):
                print(f"文件不存在: {full_path}")
                return None

            # 进行语音识别
            # 注意：直接传递文件路径给transcribe方法，而不是文件内容
            segments, info = self.whisper_model.transcribe(full_path, language="zh", beam_size=5)
            
            # 提取识别结果
            recognized_text = ''.join([segment.text for segment in segments])
            # 转换为简体中文
            simplified_text = "这是通过语音识别出的内容:"+ self.cc.convert(recognized_text)
            
            return simplified_text
            
        except Exception as e:
            raise CustomException(
                error_code=ErrorCode.UNKNOWN_ERROR,
                error_message=f"ASR处理失败: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def preprocess_inputs(self, raw_inputs: list) -> str:
        """预处理多模态输入，提取文本内容"""
        combined_text = []
        
        for input_data in raw_inputs:
            if input_data.type == 'text':
                combined_text.append(input_data.content)
            elif input_data.type == 'image':
                text = self.extract_text_from_image(input_data.file_path)
                if text:
                    combined_text.append(f"[图片内容] {text}")
            elif input_data.type == 'audio':
                print('=== in this audio ====')
                text = self.extract_text_from_audio(input_data.file_path)
                if text:
                    combined_text.append(f"[语音内容] {text}")
        
        return " ".join(combined_text)