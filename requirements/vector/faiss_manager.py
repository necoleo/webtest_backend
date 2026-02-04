import os
from contextlib import contextmanager
from typing import Optional

import faiss
import numpy as np
from django.db import connection
from dotenv import load_dotenv

from config.env_config import ENV_FILE_PATH, BASE_DIR


class FaissManager:
    """
    FAISS 向量库管理
    支持：
    向量添加/删除/搜索
    索引持久化
    """

    LOCK_NAME = 'faiss_lock'
    LOCK_TIMEOUT = 60

    def __init__(self):
        # 需求项向量数据库
        load_dotenv(ENV_FILE_PATH)
        relative_path = os.environ.get("FAISS_DB_PATH", "requirements_vectors.faiss")
        self.requirement_faiss_path = os.path.join(BASE_DIR, relative_path)
        # 确保目录存在
        self.ensure_directory_exists()
        # 相似度
        self.threshold = float(os.environ.get("SIMILARITY_THRESHOLD"))
        # index索引
        self.index: Optional[faiss.IndexIDMap] = None

    @contextmanager
    def lock(self):
        """FAISS 写锁 (MySQL GET_LOCK方法实现)"""
        cursor = connection.cursor()
        cursor.execute("SELECT GET_LOCK(%s, %s)", [self.LOCK_NAME, self.LOCK_TIMEOUT])
        try:
            yield
        finally:
            cursor.execute("SELECT RELEASE_LOCK(%s)", [self.LOCK_NAME])

    def ensure_directory_exists(self):
        """确保 FAISS 数据库文件所在目录存在"""
        directory = os.path.dirname(self.requirement_faiss_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def load_index(self):
        """从文件中加载索引"""
        if os.path.exists(self.requirement_faiss_path):
            self.index = faiss.read_index(self.requirement_faiss_path)

    def add_vector(self, vector_id, vector):
        """
        添加向量
        :param vector_id: 输入向量id
        :param vector: 输入向量
        """
        with self.lock():
            try:
                processed_vector = np.array([vector], dtype=np.float32)
                # 向量归一化
                faiss.normalize_L2(processed_vector)

                self.load_index()
                # 延迟创建索引
                if self.index is None:
                    # 获取向量的维度
                    dimension = processed_vector.shape[1]
                    # 创建内积索引
                    base_index = faiss.IndexFlatIP(dimension)
                    # 包装成自定义索引
                    self.index = faiss.IndexIDMap(base_index)

                ids = np.array([vector_id], dtype=np.int64)
                self.index.add_with_ids(processed_vector, ids)

                faiss.write_index(self.index, self.requirement_faiss_path)
                return True
            except Exception as e:
                print(f"添加向量失败: {e}")
                return False

    def remove(self, vector_id):
        """
        删除向量
        :param vector_id 向量id
        """
        with self.lock():
            try:
                self.load_index()
                if self.index is None:
                    return False
                ids = np.array([vector_id], dtype=np.int64)
                self.index.remove_ids(ids)
                faiss.write_index(self.index, self.requirement_faiss_path)
                return True
            except Exception as e:
                print(f"删除向量失败: {e}")
                return False

    def search(self, vector, threshold, number):
        """
        搜索相似向量
        :param vector: 待匹配向量
        :param threshold: 相似度(浮点数 0-1）
        :param number: 返回前 number 个相似向量
        """
        try:
            self.load_index()
            if self.index is None or self.index.ntotal == 0:
                return []
            # 转为一维数组
            query_vector = np.array([vector], dtype=np.float32)
            # 数组归一化
            faiss.normalize_L2(query_vector)
            if not isinstance(number, int):
                number = int(number)
            number = min(number, self.index.ntotal)
            # 按相似度排行，输出两个数组，分别是相似度数组、向量id数组
            # 数组格式为 [[123, 234]]
            similarity_thresholds, ids = self.index.search(query_vector, number)
            similarity_vectors = []
            # 只对比
            for i in range(len(ids[0])):
                vector_id = int(ids[0][i])
                similarity_threshold = float(similarity_thresholds[0][i])
                if vector_id != -1 and similarity_threshold > threshold:
                    similarity_vectors.append(
                        {
                            "id": vector_id,
                            "similarity_threshold": round(similarity_threshold, 4),
                        }
                    )
            return similarity_vectors
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def count(self):
        """向量总数"""
        return self.index.ntotal if self.index else 0

