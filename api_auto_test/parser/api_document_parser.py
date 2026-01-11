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

        api_interface_list = []
        for check_point, requests_list in self.json_content["paths"].items():

            for method, body in requests_list.items():

                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue

                api_interface = {}

                # 获取基础字段
                api_title = body.get("summary") or body.get("description", "")
                api_url = base_url + check_point
                method = method.upper()

                # 获取 params 字段
                if self.parse_params_in_swagger(body.get("parameters")):
                    params = self.parse_params_in_swagger(body.get("parameters"))
                else:
                    params = {}

                # 获取 request_example 字段
                if params:
                    request_example = self.generate_request_example_by_params(params)
                else:
                    request_example = ""

                # 获取 response_example 字段
                response_example = self.parse_response_example(body.get("responses"))

                api_interface["document_id"] = self.document_id
                api_interface["api_title"] = api_title
                api_interface["api_url"] = api_url
                api_interface["method"] = method
                api_interface["params"] = params
                api_interface["request_example"] = request_example
                api_interface["response_example"] = response_example

                api_interface_list.append(api_interface)
        return api_interface_list



    def parse_params_in_swagger(self, parameters_content):
        """
        统一解析 swagger 接口参数
        :param parameters_content: 接口文档的 parameters 内容
        :return: params 字典
        """
        params = {}

        type_list = ["header", "path", "query", "formData", "body"]

        if not parameters_content:
            return params

        for item in parameters_content:
            # 按参数位置划分，如 header、path、query、formData、body
            params_in = item.get("in")

            # body 有 schema 结构，需要特殊处理
            if params_in == "body":

                schema = item.get("schema", {})

                # 解析 schema 字段
                if "$ref" in schema:
                    schema = self.handle_ref_in_swagger(schema["$ref"])

                params["body"] = {
                    "name": item.get("name"),
                    "description": item.get("description", ""),
                    "required": item.get("required", False),
                    "schema": schema
                }

            # 处理其余的类型 header、path、query、formData
            elif params_in in type_list:
                params_info = {
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "description": item.get("description", ""),
                    "required": item.get("required", False),
                    "default": item.get("default"),
                }
                params.setdefault(params_in, []).append(params_info)

        return params

    def generate_request_example_by_params(self, params):
        """
        从解析后好的 params 字段里生成请求示例
        :param params: parse_params_in_swagger方法生成的 params 字段
        :return:
        """

        request_example = {}

        if "body" not in params or not params["body"].get("schema"):
            return ""

        schema = params["body"].get("schema")

        if "properties" not in schema:
            return ""

        for param_name, param_info in schema["properties"].items():

            if "example" in param_info:
                request_example[param_name] = param_info["example"]

            # 若没有示例，则返回一个符合类型的默认值
            elif param_info.get("type") == "object":
                request_example[param_name] = {}
            elif param_info.get("type") == "array":
                request_example[param_name] = []
            elif param_info.get("type") == "integer":
                request_example[param_name] = 0
            elif param_info.get("type") == "boolean":
                request_example[param_name] = False
            elif param_info.get("type") == "string":
                request_example[param_name] = ""
            else:
                request_example[param_name] = None

        # 中文不转义，格式化缩进
        return json.dumps(request_example, ensure_ascii=False, indent=2)


    def parse_response_example(self, responses_content):
        """
        从 swagger 接口文档的 responses 字段中解析出响应示例
        :param response_content: 接口的 responses 字段
        :return: response_example 字符串
        """
        if not responses_content:
            return ""

        response_data = responses_content.get("200") or responses_content.get("201")
        if not response_data:
            return ""

        schema = response_data.get("schema", {})
        if not schema:
            return ""

        # 处理 $ref 引用
        if "$ref" in schema:
            schema = self.handle_ref_in_swagger(schema["$ref"])

        # 处理 allOf 组合
        if "allOf" in schema:

            merged_properties = {}

            for item in schema["allOf"]:
                # 解析子项的 $ref
                if "$ref" in item:
                    item = self.handle_ref_in_swagger(item["$ref"])
                # 合并 properties
                if "properties" in item:
                    merged_properties.update(item["properties"])

            schema = {
                "type": "object",
                "properties": merged_properties,
            }

        # 从 properties 生成响应示例
        if "properties" in schema:
            response_example = {}

            for param_name, param_info in schema["properties"].items():
                if "$ref" in param_info:
                    param_info = self.handle_ref_in_swagger(param_info["$ref"])

                # 提取 example
                if "example" in param_info:
                    response_example[param_name] = param_info["example"]

                # 若没有示例，则返回一个符合类型的默认值
                elif param_info.get("type") == "object":
                    response_example[param_name] = {}
                elif param_info.get("type") == "array":
                    response_example[param_name] = []
                elif param_info.get("type") == "integer":
                    response_example[param_name] = 0
                elif param_info.get("type") == "boolean":
                    response_example[param_name] = False
                elif param_info.get("type") == "string":
                    response_example[param_name] = ""
                else:
                    response_example[param_name] = None

            return json.dumps(response_example, ensure_ascii=False, indent=2)

        # 如果没有 properties，直接返回 schema
        return json.dumps(schema, ensure_ascii=False, indent=2)


    def handle_ref_in_swagger(self, ref_content):
        """
        处理 swagger 里的 $ref 引用字段
        :param ref_content: swagger 里用 $ref 的字段
        :return: 将解析后的 schema
        """
        schema = {}
        if ref_content.startswith("#/definitions/"):
            definition_name = ref_content.split("/")[-1]
            schema = self.json_content.get("definitions", {}).get(definition_name, {})
        return schema


if __name__ == '__main__':

    with open("../../doc.json", "r", encoding="utf-8") as f:
        content = json.loads(f.read())

    parser = ApiDocumentParser(1, content)
    parser.parser_swagger()