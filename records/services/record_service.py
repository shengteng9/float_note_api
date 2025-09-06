
from typing import Dict, Any, Union, List
from ..models import Record, Category
from accounts.models import User
from ..llm_processor import LLMProcessor
import datetime
from typing import Dict, Optional, List
from mongoengine.queryset.visitor import Q 
from pydantic import Field, BaseModel
from ..models import RawInput
from ..cache.utils import get_cached_or_fetch, serialize_model, deserialize_dict
from ..cache.keys import record_key, records_list_key
from django.core.paginator import Paginator
import json


class RecordService:
    """记录服务类"""
    
    def __init__(self):
        self.llm_processor = LLMProcessor()
    
    def create_record_with_llm(self, title: str, raw_inputs_data: list, user: User, category_id: str) -> Record:
        """使用LLM创建记录，支持文件上传"""

        # 创建RawInput对象
        raw_inputs = []
        for input_data in raw_inputs_data:
            raw_input = RawInput(**input_data)
            raw_inputs.append(raw_input)

        # 从数据库中拿到LLM需要的分类数据，并处理成对应的格式      
        category_schema = self.getCategorySchema(user, category_id)
        
        # 使用LLM处理输入
        processing_result = self.llm_processor.process_inputs(raw_inputs, category_schema, user=user)
        
        # 创建记录
        record = Record(
            title=title,
            user=user,
            raw_inputs=raw_inputs,
            type=processing_result['type'],
            content=processing_result['content'],
            is_processed=True,
            category=processing_result['category'],
            processed_at=datetime.datetime.now()
        )

        record.save()
        return record
    
    def reprocess_record(self, record: Record) -> Record:
        """重新处理记录"""
        record.is_processed = False
        record.save()  # 会触发clean方法中的自动处理
        return record


    def getCategorySchema(self,  user: User, category_id: str) -> Optional[Dict]:
        """获取分类 schema"""
        # 构建基础查询条件：用户自己的分类、默认分类或激活的分类
        query = Q(user=user) | Q(is_default=True) 
        
        # 如果category_id不为空，则添加ID过滤条件（优先级最高）
        if category_id:
            query = query & Q(id=category_id)
            
        # 执行查询
        categories = Category.objects.filter(query)

        if not categories:
            raise Exception("用户没有分类")
        
        record_types = []
        descriptions = []
        record_field_specs = {}
        category_types = {}
        
        for category in categories:
            record_field_specs[category.name] = self.create_dynamic_schema(category.field_specs) # 用户维度下，分类不存在重名
            record_types.append(category.name)
            descriptions.append(f"类型名称:{category.name},类型描述:{category.description}。")  
            category_types[category.name] = category.id # 根据分类，拿到分类id
        record_types_description = "".join(descriptions)

        return {
            'record_field_specs': record_field_specs, # 分类字段的schema
            'record_types': record_types, # 分类的类型名称 [str, str, ...]
            'record_types_description': record_types_description, # 分类的类型描述
            'category_types': category_types, # 分类的类型名称和id的映射 {str: str, str: str, ...}
        }

    def create_dynamic_schema(self, field_specs: list) -> any:

        """格式化分类字段，变成LLM的解析schema"""

        FIELD_TYPE_MAPPING: Dict[str, Type] = {
            "number": float,    
            "string": str,  
            "list": List, 
            "object": Dict,
            "boolean": bool,
            "datetime": datetime.datetime,
        }

        model_fields: Dict[str, Any] = {}
        # 用于存储类型注解（Pydantic 依赖 __annotations__ 字典识别类型）
        model_annotations: Dict[str, Type] = {}
        for field in field_specs:
            # 提取字段基础信息
            field_name = field["name"]          # 字段名（如"income"）
            field_type_str = field["field_type"]# 字段类型字符串（如"number"）
            required = field["required"]        # 是否必填
            default_val = field["default"]      # 默认值
            description = field["description"]  # 字段描述
            # ref_model暂不处理（可根据业务扩展，如关联其他Model）

            # 1. 映射Pydantic类型（若字段类型不支持，抛出异常）
            try:
                field_type = FIELD_TYPE_MAPPING[field_type_str.lower()]
            except KeyError:
                raise ValueError(f"不支持的字段类型：{field_type_str}，请扩展FIELD_TYPE_MAPPING")

            # 2. 转换默认值类型（确保与字段类型匹配，如"0.0"→float）
            try:
                if default_val is None:
                    parsed_default = None
                elif field_type == float and isinstance(default_val, str):
                    parsed_default = float(default_val)
                elif field_type == datetime.datetime and isinstance(default_val, str):
                    parsed_default = datetime.datetime.strptime(default_val, "%Y-%m-%d %H:%M:%S") 
                else:
                    parsed_default = field_type(default_val)
            except (ValueError, TypeError):
                raise ValueError(f"字段{field_name}的默认值{default_val}与类型{field_type_str}不匹配")

            # 3. 构建 Field 约束（包含默认值、描述等）
            field_constraint = Field(
                default=parsed_default,
                required=required,
                description=description,
            )

            # 4. 关键：将字段类型添加到注解字典（确保 Pydantic 识别类型）
            #  只要默认值是 None，就用 Optional[T]
            if parsed_default is None:
                model_annotations[field_name] = Optional[field_type]
            else:
                model_annotations[field_name] = field_type
            # 5. 字段值 = Field 约束（Pydantic 会结合注解和约束）
            model_fields[field_name] = field_constraint

        model_annotations['raw_text'] = str
        model_fields['raw_text'] = Field(description="原始文本内容")

        # 添加tags字段
        model_annotations['tags'] = Union[List[str], str]

        # 构建tags字段的描述，固定字段单独处理
        tags_description = "相关的标签"
        model_fields['tags'] = Field(
            default=None,
            description=tags_description
        )
        
        # 6. 动态创建模型时，同时传入字段值和类型注解
        DynamicModel = type(
            "DynamicSchema",
            (BaseModel,),
            {
                **model_fields,  # 字段约束
                "__annotations__": model_annotations  # 类型注解（核心！）
            }
        )


        return DynamicModel


    def get_record_by_id(self, record_id):
        try:
            # 直接调用get_cached_or_fetch获取数据
            result = get_cached_or_fetch(
                record_key(record_id),
                lambda: Record.objects.get(id=record_id),
                serializer=serialize_model,
                deserializer=lambda data: deserialize_dict(data, Record),
                timeout=600
            )

            
            # 最后的安全检查，确保返回的是有效的Record对象
            if result is None:
                print(f"结果为空，抛出异常")
                raise Exception(f"记录{record_id}不存在")
            
            # 额外验证：确保结果具有Record对象应有的属性
            if not hasattr(result, 'type') or not hasattr(result, 'content'):
                print(f"结果对象缺少必要属性，重新从数据库获取")
                # 回源重新获取，不依赖缓存
                return Record.objects.get(id=record_id)
            
            return result
        except Record.DoesNotExist:
            print(f"记录{record_id}不存在于数据库")
            raise Exception(f"记录{record_id}不存在")
        except Exception as e:
            print(f"获取记录失败: {e}")
            # 捕获所有异常并重新抛出
            raise