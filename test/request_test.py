import os

import requests
from dotenv import load_dotenv

from config.env_config import ENV_FILE_PATH

if __name__ == '__main__':
    # base_url = 'http://127.0.0.1:8000'
    # login_url = f'{base_url}/api/user/login/'
    # upload_url = f'{base_url}/api/api_document/upload/'
    # get_list_url = f'{base_url}/api/api_document/list/'
    # login_data = {
    #     "username": "heypon",
    #     "password": "xiehaipeng"
    # }
    # session = requests.Session()
    # r = session.post(url=login_url, json=login_data)
    #
    # print(r)
    # session.headers.update()
    # data = {
    #     "project_id": 1,
    #     "version": "1.0.0",
    #     "comment": "测试"
    # }
    # # 准备文件（使用实际文件路径）
    # file_path = r"D:\pyproject\new_webtest\backend\doc.json"  # 测试文件路径
    # if os.path.exists(file_path):
    #     with open(file_path, 'rb') as f:
    #         files = {
    #             'file': (os.path.basename(file_path), f)
    #         }
    #
    #         # 发送 POST 请求（multipart/form-data）
    #         response = session.post(
    #             url=upload_url,
    #             data=data,  # 表单字段
    #             files=files,  # 文件
    #             timeout=30
    #         )
    #
    #         print(f"状态码: {response.status_code}")
    #         print(f"响应: {response.json()}")
    # else:
    #     print(f"测试文件不存在: {file_path}")

    # get_list_data = {
    #     "page": 1,
    #     "page_size": 20
    # }
    # get_list_respone = session.get(url=get_list_url, params=get_list_data)
    # print(get_list_respone.json())

    # 请求dify
    base_url = "https://api.dify.ai/v1/"
    load_dotenv(ENV_FILE_PATH)
    workflow_checkpoint = "workflows/run"
    dify_api_key = os.environ.get("DIFY_EMBEDDING_API_KEY")
    session = requests.Session()
    session.headers.update({
        "Authorization": f'Bearer {dify_api_key}',
        "Content-Type": "application/json"
    })
    json_data = {
        "inputs": {  # inputs 包装
            "content": "测试测试"  # content 在 inputs 里面
        },
        "response_mode": "blocking",
        "user": "test-user"
    }
    response = session.post(base_url + workflow_checkpoint, json=json_data)
    print(base_url + workflow_checkpoint)
    print(response.status_code)
    print(response.json())
    vector = response.json()["data"]["outputs"]["json"][0]["vector"][0]
    print(vector)
