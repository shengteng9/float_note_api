from typing import Dict, Any
import io
import base64
import tempfile
import os
from ..models import EventType
from faster_whisper import WhisperModel

class AudioProcessor:
    def __init__(self):
        # 初始化模型，使用单例模式避免重复加载
        self.model = None
        
    def _get_model(self):
        """懒加载模型"""
        if self.model is None:
            # 使用 base 模型，CPU 运行，int8 量化以节省内存
            self.model = WhisperModel("base", device="cpu", compute_type="int8")
        return self.model

    def process(self, audio_data: str) -> Dict[str, Any]:
        """处理音频输入"""
        try:
            # 处理base64音频
            if audio_data.startswith('data:audio'):
                audio_data = audio_data.split(',')[1]
            
            audio_bytes = base64.b64decode(audio_data)
            
            # 创建临时文件处理音频
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name
            
            try:
                # 使用 faster-whisper 进行语音识别
                model = self._get_model()
                
                # 转录音频，自动检测语言，开启VAD过滤提升效果
                segments, info = model.transcribe(
                    temp_audio_path, 
                    language=None,  # 自动检测语言
                    beam_size=5,
                    vad_filter=True
                )
                
                # 拼接所有识别片段
                text = " ".join(segment.text for segment in segments).strip()
                
                # 如果没有识别到内容
                if not text:
                    text = "[未识别到语音内容]"
                
                # 记录识别信息
                recognition_info = {
                    'detected_language': info.language,
                    'language_probability': info.language_probability,
                    'audio_length': len(audio_data)
                }
                
            finally:
                # 确保临时文件被删除
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
            
            # 使用文本处理器继续处理
            from .text_processor import TextProcessor
            text_processor = TextProcessor()
            result = text_processor.process(text)
            
            # 添加音频识别信息到结果中
            result['content'].update(recognition_info)
            
            return result
            
        except Exception as e:
            return {
                'type': EventType.UNKNOWN.value,
                'content': {
                    'error': str(e), 
                    'raw_audio': audio_data[:100] + '...' if audio_data else 'None',
                    'audio_length': len(audio_data) if audio_data else 0
                },
                'confidence': 0.0
            }
