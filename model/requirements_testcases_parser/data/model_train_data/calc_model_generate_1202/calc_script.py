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

        # 获取参考测试用例
        reference_cases_list = []
        with open(r"D:\pyproject\new_webtest\model\requirements_testcases_parser\data\model_train_data\calc_model_generate_1202\second_rlhf_train.json", 'r', encoding='utf-8') as f:
            reference_messages = json.loads(f.read())
        for reference_case in reference_messages:
            reference_cases_list.append(reference_case['messages'][2]['content'])
        count = 0
        for item in messages:
            user_to_ask_model_dict = {
                "user_content": f"{item['user']} 基于以上需求，模型生成的测试用例为：{item['answer']}",
                "assistant_content": reference_cases_list[count]
            }
            count += 1
            user_to_model_content_list.append(user_to_ask_model_dict)

        return user_to_model_content_list

    def write_test_case(self, case_dict):
        """保存测试用例文件"""
        filename = r"D:\pyproject\new_webtest\model\requirements_testcases_parser\data\model_train_data\calc_model_generate_1202\calc_cases.json"
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
                print(item['assistant_content'])
                deepseek_model_res = self.deepseek_model_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一名资深的软件测试工程师和AI训练大师，现在你训练的专门用于生成测试用例的模型生成了一批测试用例，要求你对其进行判断。你需要极其严格判断测试用例的质量，必须是无重复、符合需求场景、没有过度延伸导致超过需求范围的，以此判断是否为有效用例、准确用例、是否考虑完整。有效用例(validity)的定义为模型生成的测试用例中，语法正确、无重复、无错别字的测试用例。准确用例(precision)的定义是模型生成的测试用例中，符合需求场景、符合业务逻辑、没有超出需求范围、描述并不笼统的测试用例。是否考虑完整(is_complete)的判断标准为模型生成的测试用例是否完全覆盖了需求，是否考虑完善。模型生成的测试用例总数generate_sum。参考用例的测试用例总数reference_sum，如果参考的测试用例不符合场景，则reference_sum为0。模型生成的测试用例中符合场景的测试用例总数true_cases_sum。需计算召回率recall_rate，计算公式为true_cases_sum / reference_sum(若reference_sum为0时，则recll_rate为0)。输出格式为 { validity: true/flase(符合要求则输出 true，不符合则输出false，布尔值), precision: true/flase(符合要求则输出 true，不符合则输出false，布尔值), is_complete: true/flase(符合要求则输出 true，不符合则输出false，布尔值), generate_sum: 这里填写模型生成测试用例总数, reference_sum: 这里填写参考测试用例总数, true_cases_sum: 模型生成的符合场景的测试用例总数, recall_rate: 这里填写召回率计算结果, reason: 这里填写理由 }，确保输出的格式为json格式，不输出其他多余的内容，不要带有```}"
                        },
                        {
                            "role": "user",
                            "content": f"{item['user_content']},参考用例为{item['assistant_content']}。输出必须符合输出格式的要求"
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
                    'generate_sum': deepseek_response['generate_sum'],
                    'reference_sum': deepseek_response['reference_sum'],
                    'true_cases_sum': deepseek_response['true_cases_sum'],
                    'recall_rate': deepseek_response['recall_rate'],
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
