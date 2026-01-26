import os

from model.requirements_testcases_parser.src.parser.vector import Vector
from model.requirements_testcases_parser.src.persisitence.testcase_db import TestCaseDb


class TestCaseIndexer:

    def __init__(self):
        # 加载向量类
        self.vector_parser = Vector(faiss_path_name="test_cases_vectors")
        self.case_fields = [
            "编号",
            "标题",
            "优先级",
            "前置条件",
            "操作步骤",
            "预期结果"
        ]

    def parse_testcase_file(self, testcase_file):
        """
        解析 测试用例文件，拆分成一条条单独的测试用例
        :param module_name: 该测试用例文件对应的模块名称
        :param file:
        :return: True/False, test_cases_list
        """
        test_cases_list = []
        filename = os.path.basename(testcase_file).split(".")[0]
        try:
            with open(testcase_file, 'r', encoding='utf-8') as f:
                lines = []
                for line in f.readlines():
                    if line.strip():
                        lines.append(line)
                for line in lines[2:]:
                    parts = line.split('\t')
                    if len(parts) != len(self.case_fields):
                        print("测试用例元素不完整")
                        return False, []
                    test_case_dict = dict(zip(self.case_fields, parts))
                    test_case = self.dict_to_str(test_case_dict)
                    test_case = filename + "模块_" + test_case
                    test_cases_list.append(test_case)
            return True, test_cases_list
        except FileNotFoundError as e:
            return False, []

    def dict_to_str(self, test_case_dict):
        case_str = ""
        for field in self.case_fields:
            value = test_case_dict[field]
            value = value.replace("<br>", "\n")
            case_str += f"{field}：{value}\n"
        return case_str.rstrip("\n")  # 去除末尾多余换行

    def parse_testcases(self, testcase):
        """
        解析测试用例
        将测试用例按元素拆分字典格式
        """
        testcase_dict = {}
        testcase_moudle = testcase.split("_")[0]
        testcase_lines = testcase.split("\n")
        for line in testcase_lines:
            if '：' in line:
                key, value = line.split('：', 1)
                key = key.strip()
                value = value.strip()
                if key in self.case_fields:
                    if key == "优先级":
                        value = value.replace("P", "")
                        value = int(value)
                    if key == "标题":
                        value = testcase_moudle + "_" + value
                    testcase_dict[key] = value
        return testcase_dict


    def testcase_to_vector(self, test_case):
        try:
            testcase_vector_map = self.vector_parser.process_text_to_vector(test_case)
            return True, testcase_vector_map
        except Exception as e:
            print(f"向量转换失败：{str(e)}")
            return False, {}

    def save_testcase_vector_map(self, case_code, testcase_vector_map):
        try:
            testcase_db = TestCaseDb()
            testcase = testcase_vector_map['text']
            testcase_raw_dict = self.parse_testcases(testcase)
            testcase_dict = {
                'case_code': case_code,
                'case_title': testcase_raw_dict['标题'],
                'priority': testcase_raw_dict["优先级"],
                'precondition': testcase_raw_dict["前置条件"],
                'operation_steps': testcase_raw_dict["操作步骤"],
                'expected_result': testcase_raw_dict["预期结果"],
                'is_passed': 2,
                'is_enabled': 1,
                'is_ai_generated': 1,
                'vector_id': testcase_vector_map["vector_id"],
                'created_user': 'webtest_model'
            }
            print(testcase_dict)
            result, message = testcase_db.add_testcase_by_model(testcase_dict)
            if result:
                print("写入数据库成功")
                return True, "写入数据库成功"
            else:
                print(message)
                return False, f"写入数据库失败: {message}"
        except Exception as e:
            return False, f"写入数据库失败{str(e)}"

if __name__ == '__main__':
    test_cases = TestCaseIndexer()
    is_true, testcases_list = test_cases.parse_testcase_file('../../data/raw/test_cases_file/14【配置端】【管理端】【小程序】图片识别组合组件.txt')
    db = TestCaseDb()
    is_true2, count = db.get_next_num_model_generated()
    for test_case in testcases_list:
        is_true, testcase_map = test_cases.testcase_to_vector(test_case)
        code = "model_" + str(count)
        is_true, test_cases.save_testcase_vector_map(code, testcase_map)
        count += 1


