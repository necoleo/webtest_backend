import json


class ApiDocumentParser:
    """
    接口文档解析器
    将接口文档解析成一条条接口
    支持 swagger2.0 和 openapi3.0
    """

    def __init__(self, document_id, json_content):
        self.document_id = document_id
        self.json_content = json_content



    def check_api_document_type(self):
        """
        检测文档的类型
        支持 swagger2.0 和 openapi3.0
        :return: api_document_type (swagger、openapi、no suggest)
        """
        api_document_type = "no suggest"
        if "swagger" in self.json_content:
            api_document_type = "swagger"

        elif "openapi" in self.json_content:
            api_document_type = "openapi"

        return api_document_type


    def parser_swagger(self):

        base_url = self.json_content["host"] + self.json_content["basePath"]
        print(base_url)
        api_interface = {
            "document_id": self.document_id,
            "api_title": "",
            "api_url": "",
            "method": "",
            "params": {},
            "request_example": '',
            "response_example": "",
            "comment": "",
            "status": ""
        }

        api_interface_list = []
        for check_point, methods in self.json_content["paths"]:

            if methods.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                continue

            api_interface = {}

            api_title = methods["summary"]
            api_url = base_url + check_point
            method = methods.upper()

            response = methods["responses"]["schema"]

            api_interface["document_id"] = self.document_id
            api_interface["api_title"] = api_title
            api_interface["api_url"] = api_url
            api_interface["method"] = method












if __name__ == '__main__':

    with open("../../doc.json", "r", encoding="utf-8") as f:
        content = json.loads(f.read())

    parser = ApiDocumentParser(1, content)
    parser.parser_swagger()