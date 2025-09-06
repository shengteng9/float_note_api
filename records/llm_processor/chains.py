from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import SystemMessage
from langchain_openai import ChatOpenAI
import json

from langchain.output_parsers import (
    PydanticOutputParser,
    ResponseSchema,
    StructuredOutputParser,
)
import os
from dotenv import load_dotenv
from .schemas import SCHEMA_MAPPING, RecordType

load_dotenv()


class LLMChainFactory:
    """LLM链工厂"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
            base_url="https://api.deepseek.com/v1",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY"),  # 显式指定API密钥
            max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", 1500)),
        )


    def create_type_detection_chain(self, record_types_description: str):

        content = f"""你是一个智能类型分类器。请分析用户输入的内容，判断它属于哪种类型。可选的类型有：{record_types_description}。请只返回类型名称，不要返回其他内容。不要解释。"""

        """创建类型检测链"""
        system_message = SystemMessage(content=content)

        prompt = ChatPromptTemplate.from_messages(
            [
                system_message,
                HumanMessagePromptTemplate.from_template("用户输入：{input}"),
            ]
        )

        return prompt | self.llm

    def create_extraction_chain(
        self, record_type: str, record_field_specs: dict[str, any], tags: list = []
    ):
        """创建信息提取链 - 优化版本"""
        schema_class = record_field_specs[record_type]
        schema_info = {}
        for field_name, field_info in schema_class.schema()["properties"].items():
            schema_info[field_name] = {
                "type": field_info.get("type", "string"),
                "description": field_info.get("description", "")
            }
        parser = PydanticOutputParser(pydantic_object=schema_class)
        # format_instructions = parser.get_format_instructions()
        # 优化后  
        simplified_instructions = "请输出JSON格式，包含所有字段。不存在的信息用null。"
        # 优化标签提示 - 更简洁
        tags_prompt = ""
        if tags:
            # 只显示标签名称，不显示描述（除非描述特别重要）
            
            tag_names = [ f'{tag.name}({tag.description})' for tag in tags]
            tags_prompt = (
                f"可用标签：{','.join(tag_names)}。选1-2个相关标签,如果可用标签都不相关,则生成1个新标签。"
            )
        else:
            tags_prompt = "生成1个合适的新标签。"

        # 优化系统消息 - 更简洁直接
        system_message = SystemMessage(
            content=f"""提取结构化信息并添加标签。
    字段定义：{json.dumps(schema_info, ensure_ascii=False)}
    {tags_prompt}
    输出格式：{simplified_instructions}
    只需返回JSON，不要解释。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                system_message,
                HumanMessagePromptTemplate.from_template("输入：{input}"),
            ]
        )

        return prompt | self.llm | parser

    def create_fallback_chain(self):
        """创建备用链（当类型不确定时）"""
        system_message = SystemMessage(
            content="""你是一个通用信息提取器。请从用户输入中提取有用信息并组织成结构化数据。
尽可能识别金额、时间、地点、人物等关键信息。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                system_message,
                HumanMessagePromptTemplate.from_template("用户输入：{input}"),
            ]
        )

        return prompt | self.llm
