from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Record, Category
from .cache.utils import safe_delete
from .cache.keys import record_key, records_list_key, category_key


# 清理单条记录
@receiver(post_save, sender=Record)
@receiver(post_delete, sender=Record)
def clear_record_cache(sender, instance, **kwargs):
    safe_delete(record_key(instance.id))




@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def clear_category_cache(sender, instance, **kwargs):
    safe_delete(category_key(instance.id))