import os
from typing import Optional

import faiss
import numpy as np

from model.requirements_testcases_parser.src.model.zhipu_model import ZhiPuModel


class Vector:
    def __init__(self, faiss_path_name=None):
        # 加载模型配置
        self.zhipu_ai = ZhiPuModel()
        if faiss_path_name is None:
            faiss_path_name = "default.faiss"
        elif faiss_path_name == "requirements_vectors.faiss":
            self.type = "requirement"
        elif faiss_path_name == "test_cases_vectors.faiss":
            self.type = "testcase"
        # 继承向量库的索引
        self.faiss_path = f"../../data/processed/{faiss_path_name}.faiss"
        if os.path.exists(self.faiss_path):
            self.index = faiss.read_index(self.faiss_path)
        else:
            # index 为 faiss L2 （欧式距离）的索引
            self.index: Optional[faiss.IndexFlatL2] = None

        # 加载需求-测试用例关联向量库
        self.unified_faiss_path = f"../../data/processed/unified_vectors.faiss"
        if os.path.exists(self.unified_faiss_path):
            self.unified_index = faiss.read_index(self.unified_faiss_path)
        else:
            self.unified_index: Optional[faiss.IndexFlatL2] = None

    def process_text_to_vector(self, content):
        """
        将文本转为向量
        :param content: 文本内容
        :return: 向量索引与原文的关联字典 { vector_id: vector_id, text: content }
        """
        # 向量索引与原文的关联字典
        vector_id_to_text_dict = {
            "vector_id": "",
            "text": "",
        }

        # 调用向量模型生成向量
        is_true, zhipu_response = self.zhipu_ai.request_vector(content)
        if is_true:
            vector = zhipu_response.data[0].embedding
            # 格式化向量
            vector = np.array(vector).reshape(1, -1)

            if self.index is None:
                # 获取向量的维度
                dim = vector.shape[1]
                self.index = faiss.IndexFlatL2(dim)

            # 将当前向量写入索引
            self.index.add(vector)
            vector_id = self.index.ntotal - 1

            # 记录向量与原句子的映射关系
            vector_id_to_text_dict['vector_id'] = vector_id
            vector_id_to_text_dict['text'] = content
            # 写入faiss数据库
            faiss.write_index(self.index, self.faiss_path)

        else:
            print(zhipu_response)

        return vector_id_to_text_dict

    def save_vector_to_unified_faiss(self, vector, content):
        # 向量索引与原文的关联字典
        vector_id_to_text_dict = {
            "vector_id": "",
            "type": self.type,
            "text": ""
        }

        if self.unified_index is None:
            # 获取向量的维度
            dim = vector.shape[1]
            self.index = faiss.IndexFlatL2(dim)

        # 将当前向量写入索引
        self.unified_index.add(vector)
        vector_id = self.index.ntotal - 1

        # 记录向量与原句子的映射关系
        vector_id_to_text_dict['vector_id'] = vector_id
        vector_id_to_text_dict['text'] = content

        # 写入unified数据库

        # 写入faiss数据库
        faiss.write_index(self.index, self.unified_faiss_path)

