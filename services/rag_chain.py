
import asyncio
import hashlib
from datetime import datetime

from langchain_classic.chains.retrieval_qa.base import RetrievalQA
from langchain_openai import ChatOpenAI
from services.vector_store import vector_manager
from config.llm_conf import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, TEMPERATURE

# 导入你的缓存函数（use_rag=True 走 RAG 专用 db 15）
from cache.redis_cache import get_json_cache, set_cache


class NewsRAG:
    def __init__(self, enable_cache: bool = True):
        self.llm = ChatOpenAI(
            openai_api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            model_name=LLM_MODEL,
            temperature=TEMPERATURE
        )
        self.retriever = vector_manager.get_retriever(k=4)
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=True,
            chain_type="stuff"
        )
        self.enable_cache = enable_cache  # ：是否使用缓存

    def _get_cache_key(self, question: str) -> str:
        """生成缓存键"""
        # 使用MD5生成唯一键
        normalized = question.strip().lower()
        # 可以添加模型版本到缓存键
        cache_str = f"{normalized}|{LLM_MODEL}"
        return hashlib.md5(cache_str.encode()).hexdigest()

    async def ask(self, question: str, force_refresh: bool = False, callbacks: list = None) -> dict:
        # 1. 检查缓存
        cache_key = self._get_cache_key(question)

        if self.enable_cache and not force_refresh:
            cached = await get_json_cache(cache_key, use_rag=True)
            if cached:
                print(f"✅ 缓存命中: {question[:50]}...")
                return cached

        # 将同步操作转为异步，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        invoke = lambda q: self.qa_chain.invoke(
            q,
            config={"callbacks": callbacks} if callbacks else None,
        )
        result = await loop.run_in_executor(None, invoke, question)

        response = {
            "answer": result["result"],
            "source_news_ids": [doc.metadata["news_id"] for doc in result["source_documents"]]
        }

        # 3. 保存到缓存（新增）
        if self.enable_cache:
            await set_cache(cache_key, response, expire=3600, use_rag=True)
            print(f"💾 已缓存: {question[:50]}...")

        return response


#  生产环境使用 - 有缓存
rag = NewsRAG(enable_cache=True)

# 调试时使用 - 无缓存，每次都重新生成
rag_no_cache = NewsRAG(enable_cache=False)













