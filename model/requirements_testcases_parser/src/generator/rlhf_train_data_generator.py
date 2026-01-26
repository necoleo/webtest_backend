import json

from model.requirements_testcases_parser.src.matcher.unified_matcher import UnifiedMatcher
from model.requirements_testcases_parser.src.persisitence.requirement_mapping_db import RequirementMappingDB
from model.requirements_testcases_parser.src.persisitence.requirements_db import RequirementsDB
from model.requirements_testcases_parser.src.persisitence.testcase_db import TestCaseDb
from model.requirements_testcases_parser.src.persisitence.unified_db import UnifiedDB


class RLHFTrainDataGenerator:
    """RLHF训练数据生成器"""

    def __init__(self):
        self.requirement_db = RequirementsDB()

        self.requirement_mapping_db = RequirementMappingDB()

        self.testcases_db = TestCaseDb()

        self.unified_db = UnifiedDB()

        self.unified_matcher = UnifiedMatcher()


    def generate_for_requirement(self, requiremnt_id):
        """
        根据需求id生成训练数据
        :param requiremnt_id: 主需求的id
        :return True/False, train_data/{}: 返回json格式的message训练数据
        """

        get_requirement_content_result, mian_requirement_response = self.requirement_db.get_requirement_content_by_id(requiremnt_id)

        get_related_requirement_result, related_requirement_response = self.requirement_mapping_db.get_related_requirements(requiremnt_id)

        get_testcase_content_result, related_testcase_content_response = self.unified_matcher.get_related_testcases(requiremnt_id)

        if not get_requirement_content_result or not get_related_requirement_result or not get_testcase_content_result:
            return False, {}

        # 获取主需求文本
        main_requirement_content = mian_requirement_response['data'][0][0]

        # 获取关联需求文本
        related_requirement_content = ''
        for related_requirement in related_requirement_response['data']:
            related_requirements_map = {
                'id': '',
                'content': ''
            }
            get_related_content_result, related_requirement_content_response = self.requirement_db.get_requirement_content_by_id(int(related_requirement[0]))
            related_requirements_map['id'] = related_requirement[0]
            related_requirements_map['content'] = related_requirement_content_response['data'][0][0]
            # 拼接关联需求
            related_requirement_content += related_requirements_map['content'] + '; '

        # 获取主需求关联的测试用例
        related_testcases_list = related_testcase_content_response['data']

        # 拼接训练用的需求和关联需求
        user_content = main_requirement_content + '。需求关联的业务逻辑和关联规则为：' + related_requirement_content

        # 拼接训练用的测试用例
        assistant_content = '基于需求分析，生成以下功能测试用例。'
        for related_testcase in related_testcases_list:
            assistant_content = assistant_content + related_testcase['content'] + '; '

        train_message_list = [
            {
                'role': 'system',
                'content': '你是一名资深的软件测试工程师。你需要帮我生成功能测试用例，需要用完整的需求内容来理解业务关联和逻辑，然后结合你对业务的理解针对指定的需求内容生成需要的测试用例，需要考虑测试用例覆盖度，切忌不要生成重复的测试用例，不要创造需求'
            },
            {
                'role': 'user',
                'content': user_content
            },
            {
                'role': 'assistant',
                'content': assistant_content
            }
        ]
        # 拼接训练数据
        train_data = {
            "messages": train_message_list,
            "label": True
        }

        return True, train_data


    def generate_train_file(self, requirement_id_list, train_file_path):

        train_data = []
        for requirement_id in requirement_id_list:
            generate_result, train_message = self.generate_for_requirement(requirement_id)
            if generate_result:
                train_data.append(train_message)
        if len(train_data) == 0:
            return False, "无有效训练数据"
        try:
            with open(train_file_path, 'w', encoding='utf-8') as f:
                json.dump(
                    train_data,
                    f,
                    ensure_ascii=False,  # 保留中文原始字符
                    indent=2  # 格式化缩进，增强可读性
                )
            return True, '创建文件成功'
        except Exception as e:
            return False, f'写入文件发生错误：{str(e)}'


if __name__ == '__main__':
    rlhf = RLHFTrainDataGenerator()
    requirement_id_list = []
    for i in range(1, 74):
        requirement_id_list.append(i)
    rlhf.generate_train_file(requirement_id_list, '../../data/processed/train.jsonl')