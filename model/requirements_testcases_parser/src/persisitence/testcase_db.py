import pymysql

from model.requirements_testcases_parser.config.loader import LoadConfig


class TestCaseDb:

    def __init__(self):
        # 加载配置
        self.testcase_db_config = LoadConfig("../../config/database_config.yaml").load_config()
        self.host = self.testcase_db_config["MYSQL_HOST"]
        self.port = self.testcase_db_config["MYSQL_PORT"]
        self.username = self.testcase_db_config["MYSQL_USER"]
        self.password = self.testcase_db_config["MYSQL_PASSWORD"]
        self.database = self.testcase_db_config["MYSQL_DATABASE"]

        self.test_cases_elements = [
            'case_code',
            'case_title',
            'priority',
            'precondition',
            'operation_steps',
            'expected_result',
            'is_passed',
            'is_enabled',
            'is_ai_generated',
            'vector_id',
            'created_user'
        ]

    def add_testcase_by_model(self, testcase):
        """
        模型导入测试用例
        :param testcase: 需要存入的测试用例，{}
        :return:
        """
        if not testcase:
            return False, "参数为空"
        for element in self.test_cases_elements:
            if not element in testcase:
                return False, f"缺少参数: {element}"

        case_code = testcase["case_code"]
        case_title = testcase["case_title"]
        priority = testcase["priority"]
        precondition = testcase["precondition"]
        operation_steps = testcase["operation_steps"]
        expected_result = testcase["expected_result"]
        is_passed = testcase["is_passed"]
        is_enabled = testcase["is_enabled"]
        is_ai_generated = testcase["is_ai_generated"]
        vector_id = testcase["vector_id"]
        created_user = testcase["created_user"]

        try:
            insert_sql = f"insert into test_cases (case_code,case_title,priority,precondition,operation_steps,expected_result,is_passed,is_enabled,is_ai_generated,vector_id,created_user) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            value = (case_code,case_title,priority,precondition,operation_steps,expected_result,is_passed,is_enabled,is_ai_generated,vector_id,created_user)
            # 创建数据库连接
            requirements_db_client = pymysql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )
            cursor = requirements_db_client.cursor()
            cursor.execute(insert_sql, value)
            requirements_db_client.commit()
            cursor.close()
            requirements_db_client.close()

            return True, "写入成功"

        except Exception as e:

            return False, f"写入时发生错误: {str(e)}"

    def get_next_num_model_generated(self):
        """获取由模型入库的需求数量"""
        try:
            select_sql = "SELECT case_code FROM test_cases WHERE case_code LIKE 'model_%' ORDER BY CAST(SUBSTRING(case_code, 7) AS UNSIGNED) DESC LIMIT 1"
            # 创建数据库连接
            testcase_db_client = pymysql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )
            cursor = testcase_db_client.cursor()
            cursor.execute(select_sql)
            response = cursor.fetchall()
            if len(response) == 0:
                return True, 0
            requirement_code = response[0][0]
            str_count = requirement_code[6:]
            count = int(str_count) + 1
            testcase_db_client.commit()
            cursor.close()
            testcase_db_client.close()
            return True, count
        except Exception as e:
            print(str(e))
            return False, f"查询时发生错误：{str(e)}"

    def get_testcase_id_by_vector_list(self, vector_id_list):
        """根据向量id获取测试用例id"""
        response = {
            "code": "",
            "data": "",
            "msg": ""
        }
        int_vector_id_list = []
        for vector_id in vector_id_list:
            int_vector_id_list.append(int(vector_id))
        str_vector_list = ','.join(['%s'] * len(int_vector_id_list))
        try:
            select_sql = f"SELECT id FROM test_cases WHERE vector_id IN ({str_vector_list})"
            # 创建数据库连接
            testcases_db_client = pymysql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )
            cursor = testcases_db_client.cursor()
            cursor.execute(select_sql, int_vector_id_list)
            select_result = cursor.fetchall()
            if len(select_result) == 0:
                response["code"] = "success"
                response["message"] = "查询结果为空"
                return True, response
            response['code'] = "success"
            response['data'] = select_result
            response['message'] = "查询成功"

            return True, response
        except Exception as e:
            response["code"] = "error"
            response["message"] = f"查询失败, {str(e)}"
            return False, response

    def get_content_by_id(self, id):
        """根据id获取关联测试用例文本"""
        response = {
            "code": "",
            "data": "",
            "msg": ""
        }
        if not id:
            response['code'] = "error"
            response['message'] = "参数缺失"
        try:
            select_sql = f"SELECT case_title, priority, precondition, operation_steps, expected_result FROM test_cases WHERE id = %s"
            value = (id)
            # 创建数据库连接
            requirements_db_client = pymysql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )
            cursor = requirements_db_client.cursor()
            cursor.execute(select_sql, value)
            select_result = cursor.fetchall()
            if len(select_result) == 0:
                response["code"] = "success"
                response["message"] = "查询结果为空"
                return True, response
            response['code'] = "success"
            response['data'] = select_result
            response['message'] = "查询成功"

            return True, response
        except Exception as e:
            response["code"] = "error"
            response["message"] = f"查询失败, {str(e)}"
            return False, response