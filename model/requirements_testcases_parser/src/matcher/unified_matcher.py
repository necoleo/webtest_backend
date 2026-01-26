import faiss
import numpy as np

from model.requirements_testcases_parser.config.loader import LoadConfig
from model.requirements_testcases_parser.src.parser.vector import Vector
from model.requirements_testcases_parser.src.persisitence.requirements_db import RequirementsDB
from model.requirements_testcases_parser.src.persisitence.testcase_db import TestCaseDb
from model.requirements_testcases_parser.src.persisitence.unified_db import UnifiedDB


class UnifiedMatcher:
    def __init__(self):
        # 加载需求向量数据库
        self.vector_config = LoadConfig("../../config/vector_config.yaml").load_config()

        # 加载需求向量数据库
        self.requirement_vector_parser = Vector(faiss_path_name="requirements_vectors")
        self.requirement_faiss_name = self.vector_config['REQUIREMENT_FAISS_PATH']

        # 加载测试用例向量数据库
        self.testcase_vector_parser = Vector(faiss_path_name="test_cases_vectors")
        self.testcase_faiss_name = self.vector_config['TEST_CASES_FAISS_PATH']

        # 相似度阈值
        self.similarity_threshold = self.vector_config['UNIFIED_SIMILARITY_THRESHOLD']

    def requirement_match_testcase(self, requirement_code):
        """需求匹配测试用例"""
        """
        1. 根据需求id获取到对应需求的向量id
        2. 根据向量id获取到需求向量
        3. 在测试向量库中匹配该向量
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
        # 加载测试用例向量库索引
        testcase_vector_index = faiss.read_index(f"../../data/processed/{self.testcase_faiss_name}")

        # 加载索引的向量总数
        vector_count = testcase_vector_index.ntotal
        distances, indices = testcase_vector_index.search(format_requirement_vector, vector_count)
        # 相似的向量索引
        similar_vectors_index = []
        for dist, idx in zip(distances[0], indices[0]):
            # 距离越小越接近
            if dist < self.similarity_threshold:
                similar_vectors_index.append(idx)

        # 将需求和测试用例存入数据库
        if len(similar_vectors_index) != 0 :
            unified_db = UnifiedDB()
            testcase_db = TestCaseDb()

            # 将 numpy 类型转为 int 类型
            int_similar_vectors_index = list(map(int, similar_vectors_index))

            # 获取测试用例id
            select_testcase_result, testcases_id_response = testcase_db.get_testcase_id_by_vector_list(int_similar_vectors_index)
            testcases_id_list = []
            for testcase_id in testcases_id_response['data']:
                testcases_id_list.append(testcase_id[0])

            # 获取需求id
            requirement_vector_list = []
            requirement_vector_list.append(requirement_vector_id)
            select_requirement_result,  requirement_id_response = requirement_db.get_requirement_by_vector_list(requirement_vector_list)
            requirement_id_list = requirement_id_response['data'][0]

            for one_testcase_id in testcases_id_list:
                create_result, create_response = unified_db.create_relation(requirement_id_list[0], one_testcase_id)
                print(f"需求 {requirement_id_list[0]} 关联 测试用例 {one_testcase_id} 成功")
            return True, response

        else:
            response['code'] = 'error'
            response['message'] = '未找到匹配的测试用例'
            return False, response

    def get_related_testcases(self, requirement_id):
        """根据需求id获取关联测试用例文本"""
        response = {
            'code': '',
            'data': [],
            'message': ''
        }

        # 获取关联的测试用例id
        related_testcases_id_list = []
        unified_db = UnifiedDB()
        related__get_result, related_response = unified_db.get_testcase_by_requirement(requirement_id)
        if related__get_result and related_response['data'] != '':
            for one_related_requirement_id in related_response['data']:
                related_testcases_id_list.append(one_related_requirement_id[0])
        else:
            response['code'] = 'error'
            response['message'] = '该需求没有关联的测试用例'
            return False, response

        # 获取关联需求的文本
        testcases_db = TestCaseDb()
        for one_related_testcase_id in related_testcases_id_list:
            get_result, select_response = testcases_db.get_content_by_id(one_related_testcase_id)

            # 解析测试用例字段
            titile = f"测试用例: {select_response['data'][0][0]}_"
            priority = f"优先级: P{select_response['data'][0][1]}_"
            precondition = f"前置条件: {select_response['data'][0][2]}_"
            operation_steps = f"操作步骤: {select_response['data'][0][3]}_"
            expected_result = f"预期结果: {select_response['data'][0][4]}"

            testcases_content = f"{titile}{priority}{precondition}{operation_steps}{expected_result}"
            related_requirement_json = {
                'id': one_related_requirement_id[0],
                'content': testcases_content,
            }
            response['data'].append(related_requirement_json)

        response['code'] = 'success'
        response['message'] = '获取关联测试用例文本成功'
        print(response)
        return True, response


if __name__ == '__main__':
    unified_matcher = UnifiedMatcher()
    # unified_matcher.requirement_match_testcase("model_2")

    unified_matcher.get_related_testcases(3)
    # 获取所有需求




