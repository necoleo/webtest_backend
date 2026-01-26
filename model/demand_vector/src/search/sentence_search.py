import faiss
import numpy as np

import jieba, re
from collections import defaultdict

from demand_vector.src.config.loader import loadConfig
from demand_vector.src.db.vector_db import VectorDatabase
from demand_vector.src.embedding.zhipu_model import ZhiPu4


class SimilarSentenceSearch:
    def __init__(self, faiss_index_path):
        self.config = loadConfig().load_config()
        self.host = self.config['MYSQL_HOST']
        self.user = self.config['MYSQL_USER']
        self.password = self.config['MYSQL_PASSWORD']
        self.port = self.config['MYSQL_PORT']
        self.db = self.config['MYSQL_DATABASE']
        # 加载FAISS索引
        self.index = faiss.read_index(faiss_index_path)
        # 这里比较关键，请弄懂
        self.index.metric_type = faiss.METRIC_INNER_PRODUCT
        # self.index.metric_type = faiss.METRIC_L2
        # 初始化数据库连接
        self.vectordb = VectorDatabase(self.host, self.user, self.password, self.port, self.db)
        self.zhipu_ai = ZhiPu4()

    def load_vector_id_to_text(self, vector_id_list):
        # 从数据库中查询所有的向量ID和文本
        records = self.vectordb.query(vector_id_list)
        # 构建向量ID到文本的映射字典
        vector_id_to_text = {record['vector_id']: record['text'] for record in records}
        return vector_id_to_text

    def search(self, query_text, similarity_threshold):
        # 调用模型处理查询句子为向量
        response = self.zhipu_ai.zhipuai_request_vector(query_text)
        query_vector = response[1].data[0].embedding
        query_vector = np.array(query_vector).reshape(1, -1)

        query_vector /= np.linalg.norm(query_vector)

        # 使用索引搜索最相似的句子
        num_vectors = self.index.ntotal
        search_result = self.index.search(query_vector, num_vectors)  # 返回与查询最相似的向量
        distances, indices = search_result

        # 过滤出相似度超过阈值的向量ID
        # 这里比较关键，请弄懂
        similar_ids = [idx for dist, idx in zip(distances[0], indices[0]) if dist > similarity_threshold]

        if not similar_ids:
            return None

        vector_id_to_text = self.load_vector_id_to_text(similar_ids)

        return vector_id_to_text

    @staticmethod
    def is_valid_phrase(phrase, min_length=2, max_length=10):
        # 检查短语长度是否在指定范围内
        if min_length <= len(phrase) <= max_length:
            # 检查短语是否包含数字
            if not re.search(r'\d', phrase):
                # 检查短语是否包含非汉字字符（除了标点符号）
                if not re.search(r'[^\u4e00-\u9fa5]+', phrase):
                    return True
        return False

    def get_hot_phrases(self, n=4, top_n=None):
        # 获取文档热词组方法

        records = self.vectordb.query_all()
        if not records:
            return []

        # 对文本进行分词
        words = []
        for record in records:
            words.extend(jieba.cut(record['text']))

        # 使用n-gram统计词组出现次数
        phrase_count = defaultdict(int)
        for i in range(len(words) - n + 1):
            phrase = ' '.join(words[i:i + n])
            phrase_count[phrase] += 1

        # 按照出现次数对词组进行排序
        sorted_phrase_count = sorted(phrase_count.items(), key=lambda x: x[1], reverse=True)

        # 过滤掉短语中的标点符号
        punctuation_pattern = re.compile(r'[，。！？、：（）；“”]')
        filtered_phrases = [(punctuation_pattern.sub('', phrase), count) for phrase, count in sorted_phrase_count]

        # 去掉短语中的空格
        sorted_phrase_count = [(phrase.replace(' ', ''), count) for phrase, count in filtered_phrases]

        # 合并连续的短语
        merged_phrases = []
        prev_phrase = None
        for phrase, count in sorted_phrase_count:
            if prev_phrase and phrase.startswith(prev_phrase[:-1]):
                merged_phrases[-1] = (prev_phrase + phrase[-1], count)
            else:
                merged_phrases.append((phrase, count))
            prev_phrase = phrase

        # 过滤掉不合理或不像人类的短语
        valid_phrases = [(phrase, count) for phrase, count in merged_phrases if
                         SimilarSentenceSearch.is_valid_phrase(phrase)]

        if not top_n:
            return valid_phrases

        # 返回出现次数最多的前N个词组作为热词组
        return valid_phrases[:top_n]

    def filter_words_by_frequency(self, word_list, threshold):
        """
        过滤出出现次数大于或等于阈值的单词
        """
        # 使用列表推导式过滤出出现次数大于或等于阈值的单词
        filtered_words = [(word, count) for word, count in word_list if count >= threshold]
        return filtered_words

    def get_information_document(self):
        """
        通过智谱AI提炼文档关键信息
        """

        records = self.vectordb.query_all()
        text_values = [record['text'] for record in records]

        return text_values
