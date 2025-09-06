from typing import Dict, Any
from .chains import LLMChainFactory
from .parsers import MultiTypeOutputParser, TypeDetector
from .utils import MultiModalPreprocessor
from .schemas import RecordType
from ..models import Tag
from accounts.models import User


import time
import json
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

class LLMProcessor:
    """LLM处理器主类"""
    
    def __init__(self):
        self.chain_factory = LLMChainFactory()
        self.output_parser = MultiTypeOutputParser()
        self.type_detector = TypeDetector()
        self.preprocessor = MultiModalPreprocessor()
    
    def process_inputs(self, raw_inputs: list, category_schema: Dict[str, any], user: User) -> Dict[str, Any]:
        """处理多模态输入"""
   
        # 1. 预处理多模态输入
        combined_text = self.preprocessor.preprocess_inputs(raw_inputs)

        
        if not combined_text.strip():
            return self._create_default_response("输入内容为空")
        
        # 2. 类型检测
        record_type = self._detect_record_type(combined_text, category_schema)
        # 3. 根据分类拿到tags
        tags = self._get_tags(record_type, category_schema, user)
        # 4. 信息提取
        result = self._extract_information(record_type, combined_text, category_schema['record_field_specs'], tags)
   
        # 5. 新生成的tags
        format_tags = self._get_new_tags(result, tags, category_schema['category_types'][record_type], user)

        result['tags'] = format_tags

        # 6. 组装响应
        return {
            'type': record_type,
            'content': result,
            'raw_text': combined_text,
            'category': category_schema['category_types'][record_type],
        }
    
    def _detect_record_type(self, text: str, category_schema: Dict[str, any]) -> str:
        """检测记录类型"""
        try:
            # 使用LLM进行精确类型检测
            chain = self.chain_factory.create_type_detection_chain(record_types_description=category_schema['record_types_description'])
            response = chain.invoke({"input": text})
            # 大模型的类型检测结果
            detected_type = response.content.strip().lower()
            
            if detected_type in category_schema['record_types']:
                return detected_type

            raise ValueError(f"类型检测失败: 大模型检测到的类型{detected_type}不在可选类型列表中")

            # 如果LLM检测失败，使用关键词检测
            #return self.type_detector.detect_type(text)
            
        except Exception as e:
            print(f"类型检测失败: {e}")
            return self.type_detector.detect_type(text)

    def _get_tags(self, record_type: str, category_schema: Dict[str, any], user: User) -> list:
        """根据分类拿到tags"""
 
        category_id = category_schema['category_types'][record_type]
        tags = Tag.objects.filter(category=category_id, user=user.id)
        if tags.count() > 0:
            return tags
        else:
            return []
    
    def _get_new_tags(self, result: Dict[str, Any], tags: list, category_id: any, user: User) -> list:
        """
        从提取结果中获取新生成的tags
        
        Args:
            result: LLM提取的结果，包含tags字段，是str类型
            tags: 根据分类查到的tags，是list类型
        
        void : 创建系统生成的Tag(可能是多个)
        """
        try:
            # 从提取结果中获取新生成的tags
            tags_to_create = []
            

            result_tags = result.get('tags', []) # str
            if len(result_tags) == 0:
                raise ValueError("LLM没有对记录进行标注，无法创建新的tags")
            
            result_tags_list = [tag.strip() for tag in result_tags.split(',')]
            
            for tag in result_tags_list:
                if tag not in [t.name for t in tags]:
                    tags_to_create.append(tag)
            
            if len(tags_to_create) > 0:
                Tag.objects.insert([
                    Tag(
                        name=tag, 
                        category=category_id, 
                        user=user,
                        description='暂无描述,按语义理解',
                        system_created=True) 
                    for tag in tags_to_create
                ])
            else:
                pass
            # 调整LLM解析结果中tags的类型
            return result_tags_list
        
        except Exception as e:
            print(f"创建系统标签失败: {e}")
        

    def _extract_information(self, record_type: str, text: str, record_field_specs: Dict[str, any], tags: list) -> Dict[str, Any]:
        """
        提取结构化信息
        
        Args:
            record_type: 记录类型
            text: 输入文本
            record_field_specs: 字段规格schema
        
        Returns:
            提取到的结构化信息
        """
        try:
            chain = self.chain_factory.create_extraction_chain(record_type, record_field_specs, tags)
            result = chain.invoke({"input": text})
            return result.dict()
        except Exception as e:
            print(f"信息提取失败: {e}")
            # 使用备用链
            return ValueError(f"信息提取失败: {e}")
            # return self._fallback_extraction(text)
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """备用信息提取方法"""
        try:
            chain = self.chain_factory.create_fallback_chain()
            response = chain.invoke({"input": text})
            return {"extracted_info": response.content, "raw_text": text}
        except Exception as e:
            print(f"备用提取失败: {e}")
            return {"error": "信息提取失败", "raw_text": text}
    

    def _create_default_response(self, message: str) -> Dict[str, Any]:
        """创建默认响应"""
        return {
            'type': RecordType.UNKNOWN.value,
            'content': {'error': message},
            # 'confidence': 0.1,
            'raw_text': ''
        }