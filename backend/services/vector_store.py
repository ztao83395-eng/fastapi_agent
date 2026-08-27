from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config.llm_conf import (
    VECTOR_COLLECTION_NAME,
    VECTOR_STORE_DIR,
    get_embedding_model_kwargs,
)

class VectorStoreManager:
    _instance = None
    #第一阶段：类的定义与单例模式实现
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_store()
        return cls._instance

    #第二阶段：初始化向量库
    def _init_store(self):
        self.embeddings = OpenAIEmbeddings(**get_embedding_model_kwargs())
        self.store = Chroma(
            persist_directory=VECTOR_STORE_DIR,
            collection_name=VECTOR_COLLECTION_NAME,
            embedding_function=self.embeddings,
        )

    #第三阶段：提供相似检索器接口
    #集成到 LangChain 链（用 Retriever）
    def get_retriever(self, k=4):
        return self.store.as_retriever(search_kwargs={"k": k})

    #第四阶段：提供相似度搜索接口
    #默认返回4条最相似的结果
    #独立搜索功能（用 similarity_search）
    def similarity_search(self, query, k=4):
        return self.store.similarity_search(query, k=k)

# 全局单例
vector_manager = VectorStoreManager()
