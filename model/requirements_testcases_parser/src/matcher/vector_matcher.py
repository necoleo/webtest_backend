import faiss
import numpy as np

from model.requirements_testcases_parser.config.loader import LoadConfig
from model.requirements_testcases_parser.src.model.zhipu_model import ZhiPuModel
from model.requirements_testcases_parser.src.parser.vector import Vector
from model.requirements_testcases_parser.src.persisitence.requirements_db import RequirementsDB


class VectorMatcher:

    def __init__(self, type):
        # 加载向量配置
        self.vector_config = LoadConfig("../../config/vector_config.yaml").load_config()

        if type == "requirement":
            # 加载需求向量数据库
            self.vector_parser = Vector(faiss_path_name="requirements_vectors")
            self.faiss_path_name = self.vector_config['REQUIREMENT_FAISS_PATH']
            self.similarity_threshold = self.vector_config['REQUIREMENT_SIMILARITY_THRESHOLD']

        elif type == "testcase":
            # 加载测试用例向量数据库
            self.vector_parser = Vector(faiss_path_name="testcase")
            self.faiss_path_name = self.vector_config['TESTCASE_FAISS_PATH']
            self.similarity_threshold = self.vector_config['TEST_CASES_SIMILARITY_THRESHOLD']

        else:
            pass

        # 加载向量索引
        self.vector_index = faiss.read_index(f"../../data/processed/{self.faiss_path_name}")
        # 设置相似度判断方式
        self.vector_index.metric_type = faiss.METRIC_INNER_PRODUCT

        # 加载智谱AI模型
        self.zhipu_ai = ZhiPuModel()

    def match_vector(self, content):
        """
        向量匹配
        :param content: 要匹配的文本
        :return: is_true, similar_vectors_index, 是否成功，相似的向量索引列表
        """
        # 将需求文本转为向量
        is_true, zhipu_response = self.zhipu_ai.request_vector(content)
        if not is_true:
            return False, []
        requirement_vector = zhipu_response.data[0].embedding
        # 格式化向量
        format_requirement_vector = np.array(requirement_vector).reshape(1, -1)
        # 向量归一化
        format_requirement_vector /= np.linalg.norm(format_requirement_vector)
        # 加载索引的向量总数
        vector_count = self.vector_index.ntotal
        distances, indices = self.vector_index.search(format_requirement_vector, vector_count)
        # 相似的向量索引
        similar_vectors_index = []
        for dist, idx in zip(distances[0], indices[0]):
            # 距离越小越接近
            if dist < self.similarity_threshold:
                similar_vectors_index.append(idx)
        return True, similar_vectors_index



if __name__ == "__main__":
    vector = VectorMatcher("requirement")
    is_vector, vector_id_list = vector.match_vector("03【配置端】【小程序】答题表单_“考试组件” 分组需包含 “单选答题” 组件，该组件需支持 “单选 / 多选” 切换（对应试题组件配置界面第 1 题的 “单选” 切换功能）")
    requirement_db = RequirementsDB()
    is_true, response = requirement_db.get_requirement_by_vector_list(vector_id_list)
    print(response)