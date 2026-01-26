import faiss
import numpy as np
import re
from demand_vector.src.config.loader import loadConfig
from demand_vector.src.db.vector_db import VectorDatabase
from demand_vector.src.embedding.zhipu_model import ZhiPu4
from demand_vector.src.parsing.doc_parser import WordDocumentParser
from typing import Optional


class VectorIndexing:
    """
    向量索引
    """
    def __init__(self):
        # 加载配置
        self.config = loadConfig().load_config()

        # 获取需求文档
        self.requirements_names = self.config['REQUIREMENTS_NAME']

        # 加载智谱AI
        self.zhipu_ai = ZhiPu4()

        # index 为 faiss L2（欧式距离）的索引
        self.index: Optional[faiss.IndexFlatL2] = None

        self.vector_id_to_text = []

        # 加载数据库配置
        self.faiss_path_name = self.config['FAISS_DB_PATH']
        self.host = self.config['MYSQL_HOST']
        self.user = self.config['MYSQL_USER']
        self.password = self.config['MYSQL_PASSWORD']
        self.port = self.config['MYSQL_PORT']
        self.db = self.config['MYSQL_DATABASE']
        self.vectordb = VectorDatabase(self.host, self.user, self.password, self.port, self.db)

    def process_texts(self):
        """
        将需求文档转为向量存入向量数据库，并将数据关联存入关系数据库
        :return:
        """
        requirements_text_list = []
        # 加载需求文档
        for requirements_name in self.requirements_names:
            requirement_path = '../data/raw/' + requirements_name
            print(f"正在解析 {requirement_path}")
            parser = WordDocumentParser(requirement_path)
            sentences = parser.parse()
            requirements_text_list.append(sentences)

        # 将二维的句子列表转为一维
        # 每个元素都是一条需求句子
        merged_requirements_text_list = [sentence for sublist in requirements_text_list for sentence in sublist]

        for text in merged_requirements_text_list:
            zhipu_response = self.zhipu_ai.zhipuai_request_vector(text)
            # 模型生成的向量
            vector = zhipu_response[1].data[0].embedding
            # 将列表转为 numpy 数组
            # reshape(1, -1) 把它整理成形状 (1, 向量维度) 的二维矩阵，方便后面喂给 FAISS（FAISS 需要二维）
            vector = np.array(vector).reshape(1, -1)

            if self.index is None:
                # 获取向量的维度
                dim = vector.shape[1]
                # 初始维度定位向量最大维度
                self.index = faiss.IndexFlatL2(dim)

            # 将当前向量写入索引
            # 此时 ntotal 会 +1
            self.index.add(vector)
            # 获取到该向量的 id
            vector_id = self.index.ntotal - 1

            # 记录向量与原句子的映射关系
            self.vector_id_to_text.append((vector_id, text))

            faiss.write_index(self.index, "../data/processed/" + self.faiss_path_name)

        print('向量数据处理完毕')

        for vector_id, text in self.vector_id_to_text:
            self.vectordb.create(vector_id=vector_id, text=text)

        print('数据关联存入数据库完毕')

    def case_embedding(self, case_list):
        """
        将用例列表转换为向量并存入数据库
        :param case_list: 用例列表
        :return: 向量列表
        """

        for case in case_list:
            reponse = self.zhipu_ai.zhipuai_request_vector(case[0])
            vector = reponse[1].data[0].embedding
            vector = np.array(vector).reshape(1, -1)

            # Lazily create the index if it hasn't been created yet (for case embeddings)
            if self.index is None:
                dim = vector.shape[1]
                self.index = faiss.IndexFlatL2(dim)

            self.index.add(vector)
            vector_id = self.index.ntotal - 1
            # print(case)
            self.vectordb.create_vector_case(vector_id=vector_id, case_needs=case[0], case_info=str(case[1]))
            faiss.write_index(self.index, "../data/processed" + self.faiss_path_name)
