from abc import abstractmethod
from typing import List
from zhipuai import ZhipuAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from demand_vector.src.config.loader import loadConfig
from demand_vector.src.prompts.prompt_templates import Prompts


class BaseModel:
    def __init__(self):
        pass

    @abstractmethod
    def get_model_response(self, prompt: str, images: List[str]):
        pass


class ZhiPu4:
    def __init__(self) -> None:
        loadconfig = loadConfig()
        self.config_data = loadconfig.load_config()
        self.api_key = self.config_data['OPENAI_API_KEY']
        # 向量模型
        self.embedding_model = self.config_data['OPENAI_API_MODEL_EMBEDDING']
        # 自然语言处理模型
        self.glm4_model = self.config_data['OPENAI_API_MODEL_GLM4']
        self.max_threads = self.config_data['MAX_THREADING']

    def zhipuai_request_vector(self, input):
        try:
            client = ZhipuAI(api_key=self.api_key)
            response = client.embeddings.create(
                model=self.embedding_model,
                input=input,
            )
            return True, response
        except Exception as e:
            return False, f'zhipuai request is fail: {str(e)}'

    def zhipuai_request_text(self, messages):
        try:
            client = ZhipuAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.glm4_model,
                messages=messages,
                temperature=0.1
            )
            return True, response.choices[0].message.content
        except Exception as e:
            return False, f'zhipuai request is fail: {str(e)}'

    def concurrent_zhipuai_request_text(self, messages_list: List[List[str]]):
        # 设置线程池的最大线程数
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # 使用as_completed来迭代所有任务，获取每个任务的返回值
            futures = [executor.submit(self.zhipuai_request_text, messages) for messages in messages_list]
            responses = []
            for future in as_completed(futures):
                # 获取结果
                is_success, response = future.result()
                if is_success:
                    responses.append(response)
                else:
                    # 处理错误情况
                    print(response)
            return responses

    def split_list_by_text_length(self, input_list, threshold):
        """
        将输入的列表分割成多个子列表，每个子列表中所有文本的长度总和不超过阈值。
        :param input_list: 输入的列表
        :param threshold: 子列表中所有文本长度的总和的最大值
        :return: 分割后的列表
        """
        # 创建一个空列表来存储分割后的子列表
        split_lists = []
        # 创建一个子列表来存储当前正在处理的元素
        current_sublist = []

        # 遍历输入的列表
        for item in input_list:
            # 如果当前子列表中所有文本的长度总和加上新元素的长度后不超过阈值，则添加新元素
            if sum(len(text) for text in current_sublist) + len(item) <= threshold:
                current_sublist.append(item)
            else:
                # 如果当前子列表中所有文本的长度总和超过阈值，则添加到分割后的列表中，并创建一个新的子列表
                phrase_to_natural_language_prompts = Prompts.phrase_to_natural_language(current_sublist)
                split_lists.append(phrase_to_natural_language_prompts)
                current_sublist = [item]

        # 添加最后一个子列表，即使它的长度小于阈值
        if current_sublist:
            phrase_to_natural_language_prompts = Prompts.phrase_to_natural_language(current_sublist)
            split_lists.append(phrase_to_natural_language_prompts)

        return split_lists