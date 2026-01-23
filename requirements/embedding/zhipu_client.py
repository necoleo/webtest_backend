import os

from dotenv import load_dotenv
from zhipuai import ZhipuAI

from back.settings import BASE_DIR
from config.env_config import ENV_FILE_PATH


class ZhipuClient:
    """智谱AI API封装"""


    def __init__(self):
        load_dotenv(ENV_FILE_PATH)
        self.api_key = os.environ['ZHIPU_API_KEY']
        self.client = ZhipuAI(api_key=self.api_key)
        self.chat_model = "GLM-4-Flash"
        self.embedding_model = "embedding-3"

    def chat(self, message):
        """
        调用对话模型
        :param message:
        :return:
        """
        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                message=message,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"智谱 API 调用失败: {str(e)}")

    def get_embedding(self, content):
        """
        获取文本向量（向量化阶段使用）

        :param content: 待向量化文本
        :return: 向量列表
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=content,
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"智谱向量化失败: {str(e)}")