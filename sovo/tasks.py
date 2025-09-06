
from sovo.celery import app
# from common.utils.file_storage  import TemporaryFileStorage

@app.task
def cleanup_temp_files():
    """Celery定时任务清理临时文件"""
    print('hello...')
    # TemporaryFileStorage._cleanup_old_files()