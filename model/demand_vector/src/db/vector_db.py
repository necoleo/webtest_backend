import pymysql


class VectorDatabase:
    def __init__(self, host, user, password, port, db):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.db = db
        self.connection = None

    def connect(self):
        self.connection = pymysql.connect(host=self.host,
                                          user=self.user,
                                          password=self.password,
                                          db=self.db,
                                          port=self.port,
                                          charset='utf8mb4',
                                          cursorclass=pymysql.cursors.DictCursor)

    def close(self):
        if self.connection:
            self.connection.close()

    def create(self, vector_id, text):
        self.connect()
        with self.connection.cursor() as cursor:
            sql = "INSERT INTO vectors (vector_id, text) VALUES (%s, %s)"
            cursor.execute(sql, (vector_id, text))
        self.connection.commit()
        self.close()

    def delete(self, vector_ids):
        self.connect()
        with self.connection.cursor() as cursor:
            sql = "DELETE FROM vectors WHERE vector_id IN (%s)"
            cursor.execute(sql, (','.join(str(id) for id in vector_ids)))
        self.connection.commit()
        self.close()

    def query(self, vector_ids):
        self.connect()
        with self.connection.cursor() as cursor:
            placeholders = ', '.join(['%s'] * len(vector_ids))
            sql = f"SELECT * FROM vectors WHERE vector_id IN ({placeholders})"
            cursor.execute(sql, vector_ids)
            result = cursor.fetchall()
        self.close()
        return result

    def query_all(self):
        self.connect()
        with self.connection.cursor() as cursor:
            sql = f"SELECT text FROM vectors "
            cursor.execute(sql)
            result = cursor.fetchall()
        self.close()
        return result

    def create_needs_text(self, text, requirements):
        self.connect()
        with self.connection.cursor() as cursor:
            sql = "INSERT INTO requirements (text, requirements) VALUES (%s, %s)"
            cursor.execute(sql, (text, requirements))
        self.connection.commit()
        self.close()

    def create_needs_content_text(self, module_name, text_contents, vector_id):
        self.connect()
        with self.connection.cursor() as cursor:
            sql = "INSERT INTO needs (module_name, text_contents, vector_id) VALUES (%s, %s, %s)"
            cursor.execute(sql, (module_name, text_contents, vector_id))
        self.connection.commit()
        self.close()

    def create_needs_manage_text(self, vector_id, requirements_id, needs_info):
        self.connect()
        with self.connection.cursor() as cursor:
            sql = "INSERT INTO needs_manage (vector_id , requirements_id , needs_info) VALUES (%s, %s, %s)"
            cursor.execute(sql, (vector_id, requirements_id, needs_info))
        self.connection.commit()
        self.close()

    def query_needs_manage(self):
        self.connect()
        with self.connection.cursor() as cursor:
            sql = f"SELECT * FROM needs_manage"
            cursor.execute(sql)
            result = cursor.fetchall()
        self.close()
        return result

    def query_needs(self, needs_id):
        self.connect()
        with self.connection.cursor() as cursor:
            sql = f"SELECT module_name FROM needs where id = {needs_id}"
            cursor.execute(sql)
            result = cursor.fetchall()
        self.close()
        return result

    def create_vector_case(self, vector_id, case_needs, case_info):
        self.connect()
        with self.connection.cursor() as cursor:
            sql = "INSERT INTO systemapp_vector_case (vector_id, case_needs, case_info) VALUES (%s, %s, %s)"
            cursor.execute(sql, (vector_id, case_needs, case_info))
        self.connection.commit()
        self.close()