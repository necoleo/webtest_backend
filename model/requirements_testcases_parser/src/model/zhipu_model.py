from asyncio import as_completed
from concurrent.futures import ThreadPoolExecutor
from zhipuai import ZhipuAI

from model.requirements_testcases_parser.config.loader import LoadConfig


class ZhiPuModel:
    def __init__(self):
        # 加载模型配置
        self.model_config = LoadConfig("../../config/model_config.yaml").load_config()
        self.api_key = self.model_config['ZHIPU_API_KEY']

        # 加载向量模型配置
        self.embedding_model = self.model_config['ZHIPU_MODEL_EMBEDDING']

        # 加载自然语言处理模型配置
        self.glm4_model = self.model_config['ZHIPU_GLM4_MODEL']

        # 加载线程配置
        self.thread_config = LoadConfig("../../config/system_config.yaml").load_config()
        self.max_threads = self.thread_config['MAX_THREADING']

    def request_vector(self, content):
        try:
            zhipu_client = ZhipuAI(api_key=self.api_key)
            response = zhipu_client.embeddings.create(
                model=self.embedding_model,
                input=content,
            )
            return True, response
        except Exception as e:
            return False, f'文本向量化失败: {str(e)}'

    def request_text(self, content):
        try:
            response = self.zhipu_client.chat.completions.create(
                model=self.glm4_model,
                messages=content,
                temperature=0.1
            )
            return True, response.choices[0].message.content
        except Exception as e:
            return False, f'请求智谱AI失败: {str(e)}'


    def concurrent_request_text(self, content_list):
        # 创建线程池
        futures = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            for content in content_list:
                future = executor.submit(self.request_text, content)
                futures.append(future)

            responses = []
            for future in as_completed(futures):
                # 获取结果
                is_success, response = future.result()
                if is_success:
                    responses.append(response)
                else:
                    print(response)

            return responses
