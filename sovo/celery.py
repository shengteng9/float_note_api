import os
import sys
# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery

from celery.schedules import crontab

app = Celery('sovo')

# 配置Redis作为消息代理
app.conf.broker_url = 'redis://localhost:6379/0'
# 配置Redis作为结果存储（如果需要）
app.conf.result_backend = 'redis://localhost:6379/0'

app.conf.beat_schedule = {
    'cleanup-temp-files': {
        'task': 'sovo.tasks.cleanup_temp_files',
        'schedule': crontab(hour=23, minute=59),  
    },
}
app.conf.timezone = 'Asia/Shanghai'
app.conf.enable_utc = False

app.autodiscover_tasks(['sovo.tasks'])
