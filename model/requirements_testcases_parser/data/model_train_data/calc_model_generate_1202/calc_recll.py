# -*- coding: utf-8 -*-
import json
import os

from openai import OpenAI


class CalcScript:

    def __init__(self, file_path=''):
        self.file_path = file_path

        self.deepseek_model_client = OpenAI(
            api_key="sk-cb9eaa7012b34b36b1fb2d528b2ba233",
            base_url="https://api.deepseek.com"
        )

    def read_file(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.loads(f.read())
        except FileNotFoundError as e:
            print(f"验证文件未找到: {e}")
            return None
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None

    def get_message_item(self, json_content):

        messages = json_content
        user_to_model_content_list = []

        if not json_content:
            print("未获取到数据")
            return []

        for item in messages:
            user_to_ask_model_dict = {
                "user_content": f"{item['user']} 基于以上需求，模型生成的测试用例为：{item['answer']}",
                "assistant_content": item['assistant']
            }
            user_to_model_content_list.append(user_to_ask_model_dict)

        return user_to_model_content_list

    def write_test_case(self, case_dict):
        """保存测试用例文件"""
        filename = r"/model/requirements_testcases_parser/data/model_train_data/calc_model_generate_1202/calc_cases_01.json"
        try:
            # 先读已有数据，避免覆盖原文件
            if os.path.exists(filename):
                cases_list = json.loads(open(filename, "r", encoding="utf-8").read())
            else:
                cases_list = []
            cases_list.append(case_dict)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(cases_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"写入 {filename} 失败: {e}")

    def calc_model(self):
        try:
            messages = self.read_file()
            user_to_model_content_list = self.get_message_item(messages)
            if not user_to_model_content_list:
                print("无有效验证数据")
                return None

            for item in user_to_model_content_list:
                # 调用deepseek验证结果
                print(item['user_content'])
                deepseek_model_res = self.deepseek_model_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一名资深的软件测试工程师和AI训练大师，现在你训练的专门用于生成测试用例的模型生成了一批测试用例，要求你对其进行计算。计算模型生成的测试用例总数generate_sum，参考测试用例总数reference_sum，召回率计算公式: generate_sum/reference_sum。输出格式为 { generate_sum: (这里填写模型生成的测试用例总数，number类型）, reference_sum: (这里填写参考用例的测试用例总数，number类型）, recall_rete: (这里填写召回率，浮点数number类型) reason: 这里填写理由 }，确保输出的格式为json格式，不输出其他多余的内容}"
                        },
                        {
                            "role": "user",
                            "content": f"{item['user_content']},输出必须符合输出格式的要求"
                        },
                    ]
                )

                # 解析 deepseek 返回的结果
                print(deepseek_model_res.choices[0].message.content)
                deepseek_response = json.loads(deepseek_model_res.choices[0].message.content)

                # 写入结果
                cases_dict = {
                    'user': item['user_content'],
                    'validity': deepseek_response['validity'],
                    'precision': deepseek_response['precision'],
                    'is_complete': deepseek_response['is_complete'],
                    'reason': deepseek_response['reason'],
                }

                self.write_test_case(cases_dict)

        except Exception as e:
            print(f"验证过程出错: {e}")
            return None

if __name__ == '__main__':
    calc_script = CalcScript(file_path=r"D:\pyproject\new_webtest\model\requirements_testcases_parser\data\model_train_data\calc_model_generate_1202\fail_rlhf_test_cases.json")
    # val_script.test_ask_webtest_model()
    # val_script.test_ask_deepseek_model()
    calc_script.calc_model()
