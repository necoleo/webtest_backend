import json

from requirements.embedding.zhipu_client import ZhipuClient


class RequirementExtractor:

    def __init__(self):
        self.ai_client = ZhipuClient()


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
                            "title": str(item["title"]).strip(),
                            "content": str(item["content"]).strip(),
                        }
                    )
            return requirement_list

        except Exception as e:
            return []
