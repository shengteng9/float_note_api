class CacheError(Exception):
    """缓存操作相关的基类异常"""
    pass


class CacheKeyNotFoundError(CacheError):
    """缓存键不存在"""
    def __init__(self, key):
        super().__init__(f"缓存中未找到键: {key}")
        self.key = key


class CacheConnectionError(CacheError):
    """缓存服务连接失败"""
    def __init__(self, service, reason):
        super().__init__(f"无法连接缓存服务 {service}: {reason}")
        self.service = service
        self.reason = reason


class CacheSerializationError(CacheError):
    """序列化/反序列化失败"""
    def __init__(self, obj, format):
        super().__init__(f"序列化对象失败，格式: {format}, 对象类型: {type(obj)}")
        self.obj = obj
        self.format = format