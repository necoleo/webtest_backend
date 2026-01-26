from model.requirements_testcases_parser.config.loader import LoadConfig
from model.requirements_testcases_parser.src.parser.doc_parser import WordDocumentParser
from model.requirements_testcases_parser.src.parser.vector import Vector
from model.requirements_testcases_parser.src.persisitence.requirements_db import RequirementsDB


class RequirementIndexer():
    """需求向量索引"""

    def __init__(self):
        # 加载向量数据库
        self.vector_parser = Vector(faiss_path_name="requirements_vectors")
        # 加载向量配置
        self.vector_config = LoadConfig("../../config/vector_config.yaml").load_config()
        self.faiss_path_name = self.vector_config['REQUIREMENT_FAISS_PATH']

    """
    1. 获取需求文档文件
    2. 解析需求文档，将需求文档一条一条存入列表
    3. 调用智谱的向量模型，处理需求文档
    4. 将需求文档和向量索引存入数据库
    """
    def parse_requirement_file(self, requirement_file):
        """
        解析需求文档，拆分成一条条单独的需求句子
        :param requirement_file:
        :return:
        """
        requirements_list = []

        # 需求句子
        is_true, requirements_list = WordDocumentParser(doc_path=requirement_file).get_document_paragraphs()
        if is_true:
            return requirements_list
        else:
            return []

    def requirement_to_vector(self, requirement_content):
        try:
            # 将需求转为需求向量
            requirement_vector_map = self.vector_parser.process_text_to_vector(requirement_content)
            print(requirement_vector_map)
            return True, requirement_vector_map
        except Exception as e:
            print(f"向量转换失败：{str(e)}")
            return False, {}

    def save_requirement_vector_map(self, requirement_code, requirement_vector_map):
        try:
            requirement_db = RequirementsDB()
            requirement_dict = {
                'requirement_code': requirement_code,
                'requirement_content': requirement_vector_map['text'],
                'requirement_status': 0,
                'is_parsed': 1,
                'project_id': 0,
                'vector_id': requirement_vector_map['vector_id'],
                'created_user': 'webtest_model'
            }
            result, message = requirement_db.add_requirement(requirement_dict)
            if result:
                print("写入数据库成功")
                return True, "写入数据库成功"
            else:
                print(message)
                return False, f"写入数据库失败: {message}"
        except Exception as e:
            return False, f"写入数据库失败{str(e)}"

if __name__ == '__main__':
    requirement_indexer = RequirementIndexer()
    requirement_list = requirement_indexer.parse_requirement_file(requirement_file="../../data/raw/requirements_file/药声通销售对话卡片.docx")
    db = RequirementsDB()
    result, count = db.get_next_num_model_generated()
    for requirement in requirement_list:
        is_true, str_dict = requirement_indexer.requirement_to_vector(requirement)
        requirement_code = "model_" + str(count)
        is_pass, result = requirement_indexer.save_requirement_vector_map(requirement_code, str_dict)
        count += 1