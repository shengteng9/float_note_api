def record_key(pk):
    return f"a:record:{pk}"

def category_key(pk):
    return f"a:category:{pk}"

def records_list_key(filters: dict) -> str:
    """
    根据过滤条件生成列表缓存 key
    """
    from urllib.parse import urlencode
    import hashlib

    # 只保留非空值，并排序
    filtered = sorted((k, v) for k, v in filters.items() if v is not None)
    param_str = urlencode(filtered)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
    return f"a:records:list:{param_hash}"

def categories_list_key(filters: dict) -> str:
    """
    根据过滤条件生成分类列表缓存 key
    """
    from urllib.parse import urlencode
    import hashlib

    # 只保留非空值，并排序
    filtered = sorted((k, v) for k, v in filters.items() if v is not None)
    param_str = urlencode(filtered)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
    return f"a:categories:list:{param_hash}"