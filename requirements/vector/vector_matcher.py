from requirements.embedding.embedding_config import EmbeddingConfig
from requirements.models import RequirementModel
from requirements.vector.faiss_manager import FaissManager


class VectorMatcher:
    """向量匹配器"""

    def __init__(self):
        embedding_config = EmbeddingConfig()
        self.embedding_client = embedding_config.get_embedding_client()
        self.faiss_manager = FaissManager()

    def find_similar_requirements_by_content(self, content, threshold, number):
        """
        根据需求项内容搜索相似需求
        :param content: 需求项内容
        :param threshold: 相似度阈值
        :param number: 返回数量
        :return:
        """
        # 向量化查询需求项内容
        vector = self.embedding_client.get_embedding(content)

        # 搜索相似向量
        search_results = self.faiss_manager.search(vector, threshold, number)

        if not search_results:
            return []

        # 查询需求详情
        requirements_id_list = []
        similar_threshold_map = {}
        for search_result_item in search_results:
            requirements_id_list.append(search_result_item["id"])
            similar_threshold_map[search_result_item["id"]] = search_result_item["similarity_threshold"]

        requirements = RequirementModel.objects.filter(
            id__in=requirements_id_list,
            deleted_at__isnull=True
        )

        similar_requirements = []
        for requirement_obj in requirements:
            similar_requirements.append(
                {
                    "id": requirement_obj.id,
                    "requirement_title": requirement_obj.requirement_title,
                    "requirement_content": requirement_obj.requirement_content,
                    "module": requirement_obj.module,
                    "similarity_score": similar_threshold_map[requirement_obj.id]
                }
            )
        # 按相似度排序
        similar_requirements.sort(key=lambda x: x["similarity_score"], reverse=True)

        return similar_requirements

    def find_similar_by_requirement_id(self, requirement_id, threshold, number):
        """
        根据需求ID，搜索相似需求
        """
        try:
            requirement_obj = RequirementModel.objects.get(
                id=requirement_id,
                deleted_at__isnull=True
            )

            search_results = self.find_similar_requirements_by_content(requirement_obj.requirement_content, threshold, number)

            # 排除自身
            results = [ requirement for requirement in search_results if requirement["id"] != requirement_id ]

            return results

        except RequirementModel.DoesNotExist:
            return []
        except Exception as e:
            print(f"搜索相似需求失败: {e}")
            return []


