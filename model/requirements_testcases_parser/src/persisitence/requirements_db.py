
import pymysql

from model.requirements_testcases_parser.config.loader import LoadConfig


class RequirementsDB:
    """需求管理数据库"""

    def __init__(self):
        # 加载配置
        self.requirements_db_config = LoadConfig("../../config/database_config.yaml").load_config()
        self.host = self.requirements_db_config["MYSQL_HOST"]
        self.port = self.requirements_db_config["MYSQL_PORT"]
        self.username = self.requirements_db_config["MYSQL_USER"]
        self.password = self.requirements_db_config["MYSQL_PASSWORD"]
        self.database = self.requirements_db_config["MYSQL_DATABASE"]

        self.requirement_elements = [
            'requirement_code',
            'requirement_content',
            'requirement_status',
            'is_parsed',
            'project_id',
            'vector_id',
            'created_user'
        ]

    def add_requirement(self, requirement):
        """
         模型导入需求
        :param requirement: 需要存入的需求，{}
        :return:
        """
        if not requirement:
            return False, "参数为空"
        for element in self.requirement_elements:
            if not element in requirement:
                return False, f"缺少参数: {element}"

        requirement_code = requirement["requirement_code"]
        requirement_content = requirement["requirement_content"]
        requirement_status = requirement["requirement_status"]
        is_parsed = requirement["is_parsed"]
        project_id = requirement["project_id"]
        vector_id = requirement["vector_id"]
        created_user = requirement["created_user"]

        try:
            insert_sql = f"insert into requirements (requirement_code, requirement_content, requirement_status, is_parsed, project_id, vector_id, created_user ) values (%s, %s, %s, %s, %s, %s, %s)"
            value = (requirement_code, requirement_content, requirement_status, is_parsed, project_id, vector_id, created_user)
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
            select_sql = "SELECT requirement_code FROM requirements WHERE requirement_code LIKE 'model_%' ORDER BY CAST(SUBSTRING(requirement_code, 7) AS UNSIGNED) DESC LIMIT 1"
            # 创建数据库连接
            requirements_db_client = pymysql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )
            cursor = requirements_db_client.cursor()
            cursor.execute(select_sql)
            response = cursor.fetchall()
            if len(response) == 0:
                return True, 0
            requirement_code = response[0][0]
            str_count = requirement_code[6:]
            count = int(str_count) + 1
            requirements_db_client.commit()
            cursor.close()
            requirements_db_client.close()

            return True, count
        except Exception as e:
            return False, f"查询时发生错误：{str(e)}"


    def get_requirement_by_vector_list(self, vector_id_list):
        """通过向量id列表查询需求文本id"""
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
            select_sql = f"SELECT id FROM requirements WHERE vector_id IN ({str_vector_list})"
            # 创建数据库连接
            requirements_db_client = pymysql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )
            cursor = requirements_db_client.cursor()
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

    def get_vector_id_by_requirement_code(self, requirement_code):
        """根据 requirement_code 查询对应需求向量 id"""
        response = {
            "code": "",
            "data": "",
            "message": "",
        }
        if not requirement_code:
            response['code'] = "error"
            response['message'] = "请求参数缺失"
            return False, response
        try:
            select_sql = f"SELECT vector_id FROM requirements WHERE requirement_code = %s"
            value = (requirement_code)

            # 创建数据库连接
            requirement_db_client = pymysql.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database
            )
            cursor = requirement_db_client.cursor()
            cursor.execute(select_sql, value)
            select_result = cursor.fetchall()
            if len(select_result) == 0:
                response['code'] = "success"
                response['message'] = "查询结果为空"
                return True, response

            response['code'] = 'success'
            response['data'] = select_result[0][0]
            response['message'] = '查询成功'

            requirement_db_client.commit()
            cursor.close()
            requirement_db_client.close()

            return True, response

        except Exception as e:

            response['code'] = "error"
            response['message'] = f"查询数据库发生错误: {str(e)}"

            return False, f"<UNK>, {str(e)}"

    def get_requirement_content_by_id(self, id):
        """通过需求id查询需求文本"""
        response = {
            "code": "",
            "data": "",
            "msg": ""
        }
        if not id:
            response['code'] = "error"
            response['message'] = "参数缺失"
        try:
            select_sql = f"SELECT requirement_content FROM requirements WHERE id = %s"
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


if __name__ == '__main__':
    requirements_db = RequirementsDB()
    requirements_db.get_count_model_generated()