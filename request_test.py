import requests

if __name__ == "__main__":
    # data = {
    #     'project_code': 20022,
    #     'project_name': "测试项目3",
    #     'project_type': "测试3",
    #     'project_status': 0,
    #     'start_date': "2025-08-12",
    #     'end_date':  "2025-09-12",
    # }
    # res = requests.post("http://127.0.0.1:8000/api/project/add", json=data)
    #
    # res = requests.get("http://127.0.0.1:8000/api/project/show")

    # data = {
    #     'project_code': "",
    # }
    # res = requests.post("http://127.0.0.1:8000/api/project/delete", json=data)

    # 请求数据（JSON格式）
    data = {
        "project_code": 10022,
        "update_data": {
            "project_name": "更新后的项目名称",
            "project_status": 1,
            "description": "这是更新后的项目描述",
            "end_date": "2025-11-30"
        }
    }
    res = requests.post("http://127.0.0.1:8000/api/project/edit", json=data)
    print(res.json())