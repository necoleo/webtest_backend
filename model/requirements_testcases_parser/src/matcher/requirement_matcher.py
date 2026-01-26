import faiss
import numpy as np

from model.requirements_testcases_parser.config.loader import LoadConfig
from model.requirements_testcases_parser.src.parser.vector import Vector
from model.requirements_testcases_parser.src.persisitence.requirement_mapping_db import RequirementMappingDB
from model.requirements_testcases_parser.src.persisitence.requirements_db import RequirementsDB


class RequirementMatcher:

    def __init__(self):
        # 加载需求向量数据库
        self.vector_config = LoadConfig("../../config/vector_config.yaml").load_config()

        # 加载需求向量数据库
        self.requirement_vector_parser = Vector(faiss_path_name="requirements_vectors")
        self.requirement_faiss_name = self.vector_config['REQUIREMENT_FAISS_PATH']

        self.similarity_threshold = self.vector_config['REQUIREMENT_SIMILARITY_THRESHOLD']


    def requirement_match_related_requirement(self, requirement_code):
        """需求匹配关联需求"""
        """
        1. 根据需求id获取到对应需求的向量id
        2. 根据向量id获取到需求向量
        3. 在需求向量库中匹配该向量
        4. 将匹配的结果建立关联，存入mysql
        """
        response = {
            'code': '',
            'data': '',
            'message': ''
        }

        # 需求向量库索引
        requirement_vector_index = faiss.read_index(f"../../data/processed/{self.requirement_faiss_name}")

        # 根据需求code获取对应的向量id
        requirement_db = RequirementsDB()
        get_result, response = requirement_db.get_vector_id_by_requirement_code(requirement_code)
        if get_result and response['data'] != '':
            requirement_vector_id = response['data']
        else:
            response['code'] = 'error'
            response['message'] = '该requirement_code没有对应的vector_id'
            return False, response

        # 需求向量
        requirement_vector = requirement_vector_index.reconstruct(requirement_vector_id)
        # 格式化向量
        format_requirement_vector = np.array(requirement_vector).reshape(1, -1)
        # 向量归一化
        format_requirement_vector /= np.linalg.norm(format_requirement_vector)
        # 加载需求向量库索引
        requirement_vector_index = faiss.read_index(f"../../data/processed/{self.requirement_faiss_name}")

        # 加载索引的向量总数
        vector_count = requirement_vector_index.ntotal
        distances, indices = requirement_vector_index.search(format_requirement_vector, vector_count)
        # 相似的向量索引
        similar_vectors_index = []
        for dist, idx in zip(distances[0], indices[0]):
            # 距离越小越接近
            if dist < self.similarity_threshold:
                similar_vectors_index.append(idx)

        # 将需求和关联需求存入数据库
        if len(similar_vectors_index) != 0 :
            # 加载需求关联数据库
            requirement_mapping_db = RequirementMappingDB()

            # 将 numpy 类型转为 int 类型
            int_similar_vectors_index = list(map(int, similar_vectors_index))

            # 获取关联的需求id
            select_related_requirement_result, related_requirement_id_response = requirement_db.get_requirement_by_vector_list(int_similar_vectors_index)
            related_requirement_id_list = []
            for testcase_id in related_requirement_id_response['data']:
                related_requirement_id_list.append(testcase_id[0])

            # 获取需求id
            requirement_vector_list = []
            requirement_vector_list.append(requirement_vector_id)
            select_requirement_result,  requirement_id_response = requirement_db.get_requirement_by_vector_list(requirement_vector_list)
            requirement_id_list = requirement_id_response['data'][0]

            for one_related_requirement_id in related_requirement_id_list:
                create_result, create_response = requirement_mapping_db.create_relation(requirement_id_list[0], one_related_requirement_id)
                if create_result:
                    print(f"需求 {requirement_id_list[0]} 关联 需求 {one_related_requirement_id} 成功")
                else:
                    print(create_response["message"])

            response['code'] = 'success'
            response['message'] = '需求关联成功'
            return True, response

        else:
            response['code'] = 'error'
            response['message'] = '未找到匹配的需求'
            return False, response

    def get_related_requirement(self, requirement_id):
        """根据需求id获取关联需求"""
        response = {
            'code': '',
            'data': [],
            'message': ''
        }

        # 获取关联的需求id
        related_requirements_id_list = []
        requirement_mapping_db = RequirementMappingDB()
        related__get_result, related_response = requirement_mapping_db.get_related_requirements(requirement_id)
        if related__get_result and related_response['data'] != '':
            for one_related_requirement_id in related_response['data']:
                related_requirements_id_list.append(one_related_requirement_id[0])
        else:
            response['code'] = 'error'
            response['message'] = '该需求没有关联的需求'
            return False, response

        # 获取关联需求的文本
        requirement_db = RequirementsDB()
        for one_related_requirement_id in related_requirements_id_list:
            get_result, select_response = requirement_db.get_requirement_content_by_id(one_related_requirement_id)
            related_requirement_json = {
                'id': one_related_requirement_id,
                'content': select_response['data'][0],
            }
            response['data'].append(related_requirement_json)

        response['code'] = 'success'
        response['message'] = '获取关联需求文本成功'
        print(response)
        return True, response


if __name__ == '__main__':
    requirement_matcher = RequirementMatcher()
    # requirement_matcher.requirement_match_related_requirement("model_2")
    for i in range(0, 73):
        model_code = "model_" + str(i)
        result, response = requirement_matcher.requirement_match_related_requirement(model_code)
        print(response)