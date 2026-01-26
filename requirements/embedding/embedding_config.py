import os
from dotenv import load_dotenv
from config.env_config import ENV_FILE_PATH
from requirements.embedding.zhipu_client import ZhipuClient
from requirements.embedding.dify_client import DifyClient

class EmbeddingConfig:

    def get_embedding_client(self):
        """根据环境变量 EMBEDDING_PROVIDER 返回对应的客户端"""
        load_dotenv(ENV_FILE_PATH)
        provider = os.getenv("EMBEDDING_PROVIDER")
        if provider == 'zhipu':
            return ZhipuClient()
        elif provider == 'dify':
            return DifyClient()
        else:
            raise ValueError(f"不支持的 embedding 提供商: {provider}")
