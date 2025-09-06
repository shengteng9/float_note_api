
import os
from sovo.settings import BASE_DIR

class load_local_model:
    def __init__(self, model_name):
        self.model_name = model_name

    def load_model(self):
        model_path = os.path.join(BASE_DIR, 'common', 'ml_models', self.model_name)
        if os.path.exists(model_path):
            return model_path
        else:
            raise FileNotFoundError(f"模型 {self.model_name} 不存在")



