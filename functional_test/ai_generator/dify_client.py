import json
import os
import re

import requests
from dotenv import load_dotenv

from config.env_config import ENV_FILE_PATH


class DifyClient:
    """Dify 客户端封装"""

    def __init__(self):
        load_dotenv(ENV_FILE_PATH)
        self.api_key = os.environ['DIFY_GENERATE_TEST_CASE_KEY']
        self.base_url = "https://api.dify.ai/v1/"

    def get_test_case(self, requirement_content, relation_requirement_detail_list):
        """
        AI生成测试用例
        :param requirement_content: 需求项
        :param relation_requirement_detail_list: 关联的需求项及其测试用例
        :return: 测试用例列表
        """
        # 调用 Dify 工作流
        response = requests.post(
            url=f"{self.base_url}workflows/run",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "inputs": {
                    "requirement_content": requirement_content,
                    "relation_test_case_list": json.dumps(relation_requirement_detail_list, ensure_ascii=False)
                },
                "response_mode": "streaming",
                "user": "webtest-user"
            },
            stream=True,
            timeout=600
        )
        response.raise_for_status()

        # 解析 SSE 流，获取 workflow_finished 事件的输出
        result_text = None
        for line in response.iter_lines():
            if line and line.decode('utf-8').startswith('data: '):
                try:
                    event = json.loads(line.decode('utf-8')[6:])
                    if event.get('event') == 'workflow_finished':
                        result_text = event.get('data', {}).get('outputs', {}).get('result')
                        break
                    elif event.get('event') == 'error':
                        raise Exception(event.get('data', {}).get('error', '工作流执行错误'))
                except json.JSONDecodeError:
                    continue

        if not result_text:
            raise Exception("未获取到 Dify 输出")

        # 解析测试用例
        text = result_text.strip()

        # 尝试直接解析 JSON
        if text.startswith('{'):
            try:
                return json.loads(text).get("test_cases", [])
            except json.JSONDecodeError:
                pass

        # 从 markdown 代码块中提取
        for block in re.findall(r'```json\s*([\s\S]*?)```', text):
            try:
                data = json.loads(block.strip())
                if "test_cases" in data:
                    return data["test_cases"]
            except json.JSONDecodeError:
                continue

        raise Exception("无法解析测试用例")
