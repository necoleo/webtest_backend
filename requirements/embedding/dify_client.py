import os

import requests
from dotenv import load_dotenv

from config.env_config import ENV_FILE_PATH


class DifyClient:
    """Dify 客户端封装"""


    def __init__(self):
        load_dotenv(ENV_FILE_PATH)
        self.embedding_api_key = os.environ['DIFY_EMBEDDING_API_KEY']
        self.base_url = "https://api.dify.ai/v1/"


    def get_embedding(self, content):
        """
        获取文本向量（向量化阶段使用）

        :param content: 待向量化文本
        :return: 向量列表
        """
        try:
            embedding_workflow_url = f"{self.base_url}workflows/run"
            session = requests.Session()
            session.headers.update({
                "Authorization": f'Bearer {self.embedding_api_key}',
                "Content-Type": "application/json"
            })
            json_data = {
                "inputs": {
                    "content": content,
                },
                "response_mode": "blocking",
                "user": "test-user"
            }
            response = session.post(url=embedding_workflow_url, json=json_data)
            return response.json()["data"]["outputs"]["json"][0]["vector"][0]
        except Exception as e:
            raise Exception(f"向量化失败: {str(e)}")