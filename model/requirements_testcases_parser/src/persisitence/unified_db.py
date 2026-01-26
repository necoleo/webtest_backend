import pymysql

from model.requirements_testcases_parser.config.loader import LoadConfig


class UnifiedDB:
    def __init__(self):
        # 加载配置
        self.requirements_db_config = LoadConfig("../../config/database_config.yaml").load_config()
        self.host = self.requirements_db_config["MYSQL_HOST"]
        self.port = self.requirements_db_config["MYSQL_PORT"]
        self.username = self.requirements_db_config["MYSQL_USER"]
        self.password = self.requirements_db_config["MYSQL_PASSWORD"]
        self.database = self.requirements_db_config["MYSQL_DATABASE"]


    def create_relation(self, requirement_id, testcase_id):
        """创建需求与测试用例的关联"""
        response = {
            'code': '',
            'data': '',
            'message': '',
        }
        if not requirement_id or not testcase_id:
            response['code'] = 'error'
            response['message'] = '请求参数缺失'
            return False, response
        try:
            insert_sql = f"INSERT INTO requirement_testcase_mapping (requirement_id, testcase_id) VALUES (%s, %s)"
            value = (requirement_id, testcase_id)
            # 创建数据库连接
            unified_db_client = pymysql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )
            cursor = unified_db_client.cursor()
            cursor.execute(insert_sql, value)
            unified_db_client.commit()

            cursor.close()
            unified_db_client.close()
            response['code'] = 'success'
            response['message'] = "创建关联成功"
            return True, response

        except Exception as e:
            response['code'] = 'error'
            response['message'] = f"创建关联关系失败：{str(e)}"
            return False, response

    def get_testcase_by_requirement(self, requirement_id):
        """根据需求查询关联的测试用例"""
        response = {
            'code': '',
            'data': '',
            'message': '',
        }
        if not requirement_id:
            response['code'] = 'error'
            response['message'] = '请求参数为空'
            return False, response
        try:
            select_sql = f"SELECT testcase_id FROM requirement_testcase_mapping WHERE requirement_id = %s"
            value = (requirement_id)

            # 创建数据库连接
            unified_db_client = pymysql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )
            cursor = unified_db_client.cursor()
            cursor.execute(select_sql, value)
            select_result = cursor.fetchall()
            if len(select_result) == 0:
                response['code'] = 'success'
                response['message'] = '查询结果为空'
                return True, response
            else:
                response['code'] = 'success'
                response['data'] = select_result
                response['message'] = '查询成功'

            unified_db_client.commit()
            cursor.close()
            unified_db_client.close()

            return True, response

        except Exception as e:
            response['code'] = 'error'
            response['message'] = f'查询数据库发生错误：{str(e)}'

            return False, response

    def get_requirement_by_testcase(self, testcase_id):
        """根据测试用例查询关联的需求"""
        response = {
            'code': '',
            'data': '',
            'message': '',
        }
        if not testcase_id:
            response['code'] = 'error'
            response['message'] = '请求参数为空'
            return False, response
        try:
            select_sql = f"SELECT requirement_id FROM requirement_testcase_mapping WHERE testcase_id = %s"
            value = (testcase_id)

            # 创建数据库连接
            unified_db_client = pymysql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )
            cursor = unified_db_client.cursor()
            cursor.execute(select_sql, value)
            select_result = cursor.fetchall()
            if len(select_result) == 0:
                response['code'] = 'success'
                response['message'] = '查询结果为空'
                return True, response
            else:
                response['code'] = 'success'
                response['data'] = select_result
                response['message'] = '查询成功'

            unified_db_client.commit()
            cursor.close()
            unified_db_client.close()

            return True, response

        except Exception as e:
            response['code'] = 'error'
            response['message'] = f'查询数据库发生错误：{str(e)}'

            return False, response
