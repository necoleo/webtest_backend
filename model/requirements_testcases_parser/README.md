backend/demand_vector/
├── data/
│   ├── processed/
│   │   ├── requirements_vectors.faiss    # 需求向量库
│   │   ├── test_cases_vectors.faiss      # 测试用例向量库
│   │   └── unified_vectors.faiss         # 统一向量库（可选）
│   └── raw/
│       ├── requirements/                 # 需求文档
│       └── test_cases/                   # 测试用例文档
├── src/
│   ├── matching/
│   │   ├── requirement_matcher.py        # 需求匹配器
│   │   ├── testcase_matcher.py           # 测试用例匹配器
│   │   └── unified_matcher.py            # 统一匹配器
│   └── indexing/
│       ├── requirement_indexer.py        # 需求向量索引
│       ├── testcase_indexer.py           # 测试用例向量索引
│       └── hybrid_indexer.py             # 混合索引器