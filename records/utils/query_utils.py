from django.db.models import Q

def build_record_query(params, user):
    """构建复杂查询条件"""
    query = Q(user=user)
    
    if category_id := params.get('category'):
        query &= Q(category=category_id)
    
    if tags := params.getlist('tags'):
        query &= Q(tags__all=tags)
    
    if date_range := params.get('date_range'):
        start, end = parse_date_range(date_range)
        query &= Q(created_at__gte=start, created_at__lte=end)
    
    return query