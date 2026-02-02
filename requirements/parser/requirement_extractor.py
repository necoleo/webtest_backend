import json
import os

import requests
from dotenv import load_dotenv

from config.env_config import ENV_FILE_PATH
from requirements.embedding.zhipu_client import ZhipuClient


class RequirementExtractor:

    def __init__(self):
        self.ai_client = ZhipuClient()
        load_dotenv(ENV_FILE_PATH)
        self.extract_requirement_key = os.environ['DIFY_REQUIREMENT_DOCUMENT_PARSE_KEY']


    def extract_requirement_document(self, requirement_document_content):
        """
        调用 AI 处理需求文档
        :param requirement_document_content:
        :return: requirement_list 需求项列表
        """
        system_prompt = {
            "role": "system",
            "content": '你是一个资深的需求分析师，可以从需求文档中提取出所有需求项。规则:1.每条需求独立提取;2.只提取功能需求，跳过背景、目录等;3.保持原文表述，不要创造;4.不允许创造不存在的需求;5.严格按照输出格式输出。输出格式:输出 JSON 数组 [{"title": "简短标题", "content":"需求详细内容"}]。若无需求则返回 []'
        }

        user_prompt = {
            "role": "user",
            "content": requirement_document_content,
        }

        message = [
            system_prompt,
            user_prompt
        ]

        chat_response = self.ai_client.chat(message)

        try:

            # 解析 json
            requirement_items = json.loads(chat_response)


            requirement_list = []
            for item in requirement_items:
                if isinstance(item, dict) and "title" in item and "content" in item:
                    requirement_list.append(
                        {
                            "requirement_title": str(item["title"]).strip(),
                            "requirement_content": str(item["content"]).strip(),
                        }
                    )
            return requirement_list

        except Exception as e:
            return []


    def extract_requirement_document_by_dify(self, requirement_document_file_url: str) -> list:
        """
        调用 Dify 工作流处理需求文档
        :param requirement_document_file_url: 需求文档文件的 URL
        :return: 需求项列表
        """
        dify_workflow_url = "https://api.dify.ai/v1/workflows/run"
        headers = {
            "Authorization": f'Bearer {self.extract_requirement_key}',
            "Content-Type": "application/json"
        }
        
        json_data = {
            "inputs": {
                "requirement_document_file": {
                    "type": "document",
                    "transfer_method": "remote_url",
                    "url": requirement_document_file_url
                }
            },
            "response_mode": "streaming",
            "user": "webtest-user"
        }
        
        response = requests.post(
            url=dify_workflow_url,
            headers=headers,
            json=json_data,
            stream=True,
            timeout=600
        )
        
        # 解析 SSE 事件流，获取最终输出
        requirement_list_str = None
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        event_data = json.loads(line_str[6:])
                        if event_data.get('event') == 'workflow_finished':
                            outputs = event_data.get('data', {}).get('outputs', {})
                            requirement_list_str = outputs.get("requirement_list") or outputs.get("text")
                    except:
                        continue
        
        if not requirement_list_str:
            print("未获取到输出")
            return []
        
        # 解析 JSON
        try:
            return json.loads(requirement_list_str)
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            print(f"原始输出前500字符: {requirement_list_str[:500]}")
            return []


if __name__ == '__main__':
    extractor = RequirementExtractor()
    result = extractor.extract_requirement_document_by_dify(
        "https://heypon-1347960590.cos.ap-guangzhou.myqcloud.com/webtest/webtest_requirement_document/4/PRD.pdf"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))