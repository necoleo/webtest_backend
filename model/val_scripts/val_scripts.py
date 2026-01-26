import json
import os
from platform import system

import requests
from dotenv import load_dotenv
from openai import OpenAI


class ValScript:
    """
    验证脚本
    用于验证训练后的模型
    """
    def __init__(self, val_file_path="C:/Users/92700/Desktop/药声通学习中心测试用例_RLHF训练数据_已填充.json"):
        """
        :param val_file_path: 验证数据集的文件路径
        """
        self.val_file_path = val_file_path
        self.model = "webtest_model"

        # load_dotenv("../../../config/.env")
        self.webtest_model_client = OpenAI(
            api_key='EMPTY',  # 需根据服务要求填写（即使为空，通常也是必填参数）
            base_url=f'http://175.178.13.247:8888/v1'  # 必须指向正确的模型服务地址
        )

        self.deepseek_model_client = OpenAI(
            api_key="sk-cb9eaa7012b34b36b1fb2d528b2ba233",
            base_url = "https://api.deepseek.com"
        )

    def read_val_file(self):
        """读取验证数据集"""
        try:
            with open(self.val_file_path, "r", encoding="utf-8") as f:
                return json.loads(f.read())
        except FileNotFoundError as e:
            print(f"验证文件未找到: {e}")
            return None
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None

    def get_message_item(self, json_content):
        """获取验证数据集数据"""
        val_messages = json_content
        user_to_model_content_list = []

        if not json_content:
            print("未获取到数据")
            return []

        for item in val_messages:
            user_to_ask_model_dict = {
                "system_prompt": item["messages"][0]["content"],
                "user_content": f"。以下是需求文档：{item['messages'][1]['content']}",
                "assistant_content": item["messages"][2]["content"]
            }
            user_to_model_content_list.append(user_to_ask_model_dict)

        return user_to_model_content_list

    def write_test_case(self, case_dict, is_pass):
        """保存测试用例文件"""
        filename = r"D:\pyproject\new_webtest\model\val_scripts\pass_test_cases.json" if is_pass else r"D:\pyproject\new_webtest\model\val_scripts\fail_test_cases.json"
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



    def val_model(self):
        """
        请求训练后的模型
        :param messages:
        :param model: 模型类型，默认为 deepseek-chat
        :param stream_option: 输出方式，false为非流式，true为流式
        :return:
        """
        try:
            val_message = self.read_val_file()
            user_to_model_content_list = self.get_message_item(val_message)

            if not user_to_model_content_list:
                print("无有效验证数据")
                return None

            for item in user_to_model_content_list:
                print(item['system_prompt'])
                print(item['user_content'])
                webtest_model_res = self.webtest_model_client.chat.completions.create(
                    model= self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": f"{item['system_prompt']}，只输出测试用例，不输出其他任何内容"
                        },
                        {
                            "role": "user",
                            "content": f"{item['user_content']}"
                        },
                    ],
                    stream=False
                )

                webtest_response = webtest_model_res.choices[0].message.content

                # 调用deepseek验证结果
                deepseek_model_res = self.deepseek_model_client.chat.completions.create(
                    model = "deepseek-chat",
                    messages = [
                        {
                            "role": "system",
                            "content": f"{'你是一名资深的软件测试工程师，有着非常丰富的软件测试经验和测试用例编写经验。现需要检查实习生写的测试用例是否符合需求文档的要求。输出格式为 { result: true/false(符合要求则输出 true，不符合则输出false，布尔值), reason: 这里填写理由 }，确保输出的格式为json格式，不输出其他多余的内容'}"
                        },
                        {
                            "role": "user",
                            "content": f"参考的测试用例为{item['assistant_content']}，实习生写的测试用例为{webtest_response},输出必须符合输出格式的要求"
                        },
                    ]
                )

                # 解析 deepseek 返回的结果
                print(deepseek_model_res.choices[0].message.content)
                deepseek_response = json.loads(deepseek_model_res.choices[0].message.content)

                # 写入结果
                cases_dict = {
                    'system': item['system_prompt'],
                    'user': item['user_content'],
                    'answer': webtest_response,
                    'assistant': deepseek_response['reason'],
                }

                self.write_test_case(cases_dict, deepseek_response["result"])

        except Exception as e:
            print(f"验证过程出错: {e}")
            return None

    def test_ask_webtest_model(self):
        val_message = self.read_val_file()
        user_to_model_content_list = self.get_message_item(val_message)

        for item in user_to_model_content_list:
            print(item['system_prompt'])
            print(item['user_content'])
            webtest_model_res = self.webtest_model_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"{item['system_prompt']}"
                    },
                    {
                        "role": "user",
                        "content": f"{item['user_content']}"
                    },
                ],
                stream=False
            )
            webtest_response = webtest_model_res.choices[0].message.content
            print(webtest_response)
            with open('model_test.txt', 'a', encoding='utf-8') as f:
                f.write(webtest_response)



    def test_ask_deepseek_model(self):
        # 读取webtest_model保存的数据
        with open('model_test.txt', 'r', encoding='utf-8') as f:
            messages = f.read()
        system_prompt = "你需要帮我生成功能测试用例。你生成测试用例的思考方向应该是：业务规则"
        user_content = "以下是需求文档：智能助手用药知识收藏功能，用药知识的答案支持收藏，收藏后可在「我的」-「我的收藏」-「用药知识」中查看。需求关联的业务逻辑和关联规则为：收藏操作需要用户登录，收藏成功后按收藏时间倒序排列"
        assistant_cases = "基于业务规则的测试用例：\n\n**测试用例1：游客收藏用药知识验证**\n- 优先级：P2\n- 前置条件：用户未登录系统\n- 操作步骤：1.进入智能助手用药知识页面;2.点击收藏按钮\n- 预期结果：1.系统自动保存收藏记录;2.无需登录即可在本地「我的收藏」查看\n\n**测试用例2：收藏排序规则验证**\n- 优先级：P3\n- 前置条件：用户已登录并收藏3条用药知识\n- 操作步骤：1.按时间顺序依次收藏3条内容;2.进入收藏列表\n- 预期结果：1.收藏列表按收藏时间正序排列;2.最早收藏的内容显示在最上方"
        deepseek_model_res = self.deepseek_model_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"{'你是一名资深的软件测试工程师，有着非常丰富的软件测试经验和测试用例编写经验。现需要检查实习生写的测试用例是否符合需求文档的要求。输出格式为 { result: true/false(符合要求则输出 true，不符合则输出false), reason: 这里填写理由 }，确保输出的格式为json格式'}"
                },
                {
                    "role": "user",
                    "content": f"参考的测试用例为{assistant_cases}，实习生写的测试用例为{messages}"
                },
            ]
        )
        # 解析 deepseek 返回的结果
        deepseek_response = json.loads(deepseek_model_res.choices[0].message.content)
        print(deepseek_response)
        # 写入结果
        cases_dict = {
            'system': system_prompt,
            'user': user_content,
            'answer': messages,
            'assistant': deepseek_response['reason'],
        }
        self.write_test_case(cases_dict, deepseek_response["result"])

if __name__ == '__main__':
    val_script = ValScript(val_file_path=r"D:\pyproject\new_webtest\model\val_scripts\first_train_data.json")
    # val_script.test_ask_webtest_model()
    # val_script.test_ask_deepseek_model()
    val_script.val_model()

