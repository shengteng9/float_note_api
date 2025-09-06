import json
from django.core.exceptions import ValidationError
def parse_json_field(querydict, key, default=None):
    """
    安全解析可能为 JSON 字符串或已结构化数据的字段
    兼容：
      - 'raw_inputs': ['[{"t":"t"}]']   → 字符串化 JSON
      - 'raw_inputs': [[{"t":"t"}]]     → 测试环境传的 list
      - 'raw_inputs': [{"t":"t"}]       → 单个 dict
    """
    if key not in querydict:
        return default

    value = querydict[key]

    # Step 1: 脱掉 QueryDict 的 list 套装
    if isinstance(value, list) and len(value) > 0:
        value = value[0]
    elif isinstance(value, list):
        return default  # 空列表

    # Step 2: 判断真实类型
    if isinstance(value, (dict, list)):
        return value  # 已是 Python 结构，直接返回

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError({key: 'JSON 格式错误'})

    raise ValidationError({key: '不支持的数据类型'})