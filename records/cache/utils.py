from django.core.cache import cache
import json
from bson import json_util
from bson.objectid import ObjectId
from contextlib import suppress
from .exceptions import CacheError

# 默认 TTL：5 分钟
DEFAULT_TIMEOUT = 300


def serialize_model(data) -> str:
    """序列化MongoEngine文档"""
    try:
        # 检查是否是MongoEngine文档实例
        if hasattr(data, 'to_mongo'):
            # 使用to_mongo()方法获取原始BSON数据，然后转换为字典
            data_dict = data.to_mongo().to_dict()

            # 处理ObjectId和其他BSON类型
            return json.dumps(data_dict, default=str)
        
        # 检查是否有to_dict方法
        elif hasattr(data, 'to_dict'):
            return json.dumps(data.to_dict(), default=str)
        
        # 处理查询集（多个对象）
        elif hasattr(data, '__iter__') and not isinstance(data, (str, dict)):
            try:
                # 尝试转换为列表并序列化每个对象
                items = []
                for item in data:
                    if hasattr(item, 'to_mongo'):
                        items.append(item.to_mongo().to_dict())
                    elif hasattr(item, 'to_dict'):
                        items.append(item.to_dict())
                    else:
                        items.append(item)
                return json.dumps(items, default=str)
            except:
                # 如果迭代失败，使用默认序列化
                return json.dumps(list(data), default=str)
        
        # 处理普通数据类型
        elif isinstance(data, (dict, list, str, int, float, bool, type(None))):
            return json.dumps(data, default=str)
        
        else:
            # 其他类型，尝试转换为字符串
            return json.dumps(str(data), default=str)
            
    except Exception as e:
        # 出错时尝试基本序列化
        try:
            return json.dumps(data, default=str)
        except:
            return json.dumps({"error": "serialization_failed", "data": str(data)})

def deserialize_dict(data_str: str, model_class) -> any:
    """反序列化到指定模型类，确保返回有效的模型对象或数据，永不返回字符串"""


    try:
        # 如果已经是字典，直接使用（可能已经反序列化过了）
        if isinstance(data_str, dict):
            data = data_str
        else:
            # 尝试解析JSON字符串
            data = json.loads(data_str)
        # 处理单个对象
        if isinstance(data, dict):
            # 处理 ObjectId 转换
            if '_id' in data and isinstance(data['_id'], str):
                try:
                    data['_id'] = ObjectId(data['_id'])
                except:
                    print(f"ObjectId转换失败: {data['_id']}")
                    pass  # 如果转换失败，保持原样
            
            # 确保有效的模型类
            if model_class and hasattr(model_class, '_fields'):
                try:
                    # 为MongoEngine模型创建实例时，需要移除_id字段，因为它是自动管理的
                    # 创建数据副本以避免修改原始数据
                    data_copy = data.copy()
                    # 保存原始_id值
                    original_id = data_copy.pop('_id', None)
                    
                    # 使用不包含_id的数据创建模型实例
                    instance = model_class(**data_copy)
                    
                    # 如果有原始_id，并且实例没有自动生成的id，则手动设置
                    if original_id and not hasattr(instance, 'id'):
                        instance.id = original_id
                    
                    # 验证创建的实例是否有效
                    if not hasattr(instance, 'type'):
                        raise CacheError("创建的模型实例缺少必要属性")
                    return instance
                except Exception as e:
                    print(f"创建模型实例失败: {e}")
                    # 如果创建模型实例失败，抛出异常而不是返回原始数据
                    raise CacheError(f"创建模型实例失败: {e}")
            else:
                # 如果没有模型类，至少确保返回的是字典而不是字符串
                if not isinstance(data, dict):
                    raise CacheError("反序列化结果不是字典类型")
                return data
        
        # 处理列表
        elif isinstance(data, list):
            if model_class and hasattr(model_class, '_fields'):
                return [model_class(**item) for item in data]
            else:
                return data  # 没有有效的模型类，返回原始数据
        
        # 其他类型 - 都视为失败
        else:
            print(f"反序列化得到非预期类型: {type(data)}")
            raise CacheError(f"反序列化得到非预期类型: {type(data)}")
            
    except json.JSONDecodeError:
        # 如果不是JSON字符串，记录错误并抛出异常
        print(f"JSON解析失败: {data_str}")
        raise CacheError(f"JSON解析失败: {data_str}")
    except Exception as e:
        print(f"反序列化错误: {e}")
        # 出错时抛出异常，让上层处理
        raise CacheError(f"反序列化错误: {e}")

def safe_get(key: str, model_class=None):
    """安全获取缓存"""
    try:
        result = cache.get(key)
        if result is None:
            return None
        
        if model_class and isinstance(result, str):
            return deserialize_dict(result, model_class)
        return result
    except Exception as e:
        print(f"[Cache] 获取失败 {key}: {e}")
        return None

def safe_set(key: str, value, timeout=300, model_class=None):
    """安全设置缓存"""
    try:
        # 如果是模型实例，先序列化
        if model_class and hasattr(value, 'to_dict'):
            value = serialize_model(value)
        
        result = cache.set(key, value, timeout)
        return result
    except Exception as e:
        print(f"[Cache] 设置失败 {key}: {e}")
        return False

def safe_delete(key: str):
    """安全删除缓存"""
    with suppress(Exception):
        cache.delete(key)

def get_cached_or_fetch(
    key: str,
    fetch_func,
    timeout=DEFAULT_TIMEOUT,
    serializer=None,
    deserializer=None
):
    """
    缓存核心：先读缓存，未命中则回源
    支持自定义序列化（如模型对象）
    """
    # 1. 尝试从缓存读取
    cached = safe_get(key)

    
    # 如果缓存数据存在且不是字符串类型，直接返回
    if cached is not None and not isinstance(cached, (str, bytes)):
        print(f'缓存数据不是字符串类型，直接返回: {type(cached)}')
        return cached
    
    # 如果有反序列化函数且缓存数据是字符串，尝试反序列化
    if cached is not None and deserializer and isinstance(cached, (str, bytes)):
        try:
            # 尝试反序列化
            deserialized = deserializer(cached)
            
            # 验证反序列化结果
            if deserialized is not None and not isinstance(deserialized, str):
                return deserialized
            else:
                print(f'反序列化结果无效或为字符串，继续回源')
        except CacheError:
            print('捕获到CacheError，继续回源')
        except Exception as e:
            print(f'反序列化过程中出现其他异常: {e}')
    
    # 如果缓存不存在、反序列化失败或结果无效，继续回源查询（不返回缓存数据）

    # 2. 缓存未命中，回源查询
    try:
        data = fetch_func()
        # 3. 写入缓存
        save_data = serializer(data) if serializer else data
        safe_set(key, save_data, timeout)
        return data
    except Exception as e:
        # 即使数据库出错，也不应让缓存问题雪崩
        print(f"[Cache] 回源失败: {e}")
        raise