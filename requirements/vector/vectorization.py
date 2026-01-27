from requirements.embedding.embedding_config import EmbeddingConfig
from requirements.models import RequirementModel
from requirements.vector.faiss_manager import FaissManager


class Vectorization:
    """
    需求项向量化
    支持：
    单个需求项向量化
    多个需求项批量向量化
    根据需求文档进行需求项向量化
    重新生成向量
    """
    def __init__(self):
        config = EmbeddingConfig()
        self.client = config.get_embedding_client()
        self.faiss_manager = FaissManager()

    def vectorize_requirement(self, requirement_id):
        """
        将单个需求向量化
        :param requirement_id: 需求ID
        :return: {
            "result": boolean,
            "message": string
        }
        """
        try:
            # 获取需求
            requirement_obj = RequirementModel.objects.get(
                id=requirement_id,
                deleted_at__isnull=True
            )

            # 检查该需求是否向量化
            if requirement_obj.is_vectorized:
                return {
                    "result": False,
                    "message": "该需求项已向量化"
                }

            # 将需求项的requirement_content字段向量化
            vector = self.client.get_embedding(requirement_obj.requirement_content)

            # 存入faiss
            self.faiss_manager.add_vector(requirement_obj.id, vector,)

            # 更新数据库标记
            requirement_obj.is_vectorized = True
            requirement_obj.vector_index = requirement_id
            requirement_obj.save(update_fields=["is_vectorized", "vector_index"])

            return {
                "result": True,
                "message": f"需求id{requirement_id} 向量化成功"
            }

        except RequirementModel.DoesNotExist:
            return {
                "result": False,
                "message": f"需求 {requirement_id} 不存在"
            }
        except Exception as e:
            return {
                "result": False,
                "message": f"向量化失败: {str(e)}"
            }

    def batch_vectorize_requirement(self, requirement_id_list):
        """
        批量向量化
        :param requirement_id_list:
        :return: {
            "success_count": int,
            "fail_count": int,
            "result": list:
        }
        """

        result_list = []
        success_count = 0
        fail_count = 0
        for requirement_id in requirement_id_list:
            vector_result = self.vectorize_requirement(requirement_id)
            result_list.append(
                {
                    "requirement_id": requirement_id,
                    **vector_result
                }
            )
            if vector_result["result"]:
                success_count += 1
            else:
                fail_count += 1

        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "result": result_list
        }

    def vectorize_by_requirement_document(self, requirement_document_id):
        """
        将指定需求文档下的所有需求项向量化
        """
        # 查询该文档下所有未向量化的需求项
        requirements_obj = RequirementModel.objects.get(
            requirement_document_id = requirement_document_id,
            is_vectorized = False,
            deleted_at__isnull=True
        ).values_list("id", flat=True)

        requirement_list = list(requirements_obj)

        if not requirement_list:
            return {
                "success_count": 0,
                "fail_count": 0,
                "result": "没有需要向量化的需求项"
            }

        result = self.batch_vectorize_requirement(requirement_list)
        return result

    def re_vectorize_requirement(self, requirement_id):
        """
        重新向量化（需求项内容更新后调用）
        :param requirement_id:
        :return: {
            "result": boolean,
            "message": string
        }
        """
        try:
            requirement_obj = RequirementModel.objects.get(
                id = requirement_id,
                deleted_at__isnull=True
            )

            vector = self.client.get_embedding(requirement_obj.requirement_content)

            # 删除旧向量
            self.faiss_manager.remove(requirement_id)
            # 添加新新向量
            self.faiss_manager.add_vector(requirement_id, vector)

            # 更新数据库
            requirement_obj.is_vectorized = True
            requirement_obj.vector_index = requirement_id
            requirement_obj.save(update_fields=["is_vectorized", "vector_index"])

            result = {
                "result": True,
                "message": f"需求 {requirement_id} 不存在"
            }
            return result

        except RequirementModel.DoesNotExist:
            result = {
                "result": False,
                "message": f"需求 {requirement_id} 不存在"
            }
            return result

        except Exception as e:
            result = {
                "result": False,
                "message": f"重新向量化失败: {str(e)}"
            }
            return result