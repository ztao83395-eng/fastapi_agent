
import asyncio
import hashlib
import logging
import re
from datetime import datetime

from langchain_classic.chains.retrieval_qa.base import RetrievalQA
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from sqlalchemy import or_, select

from config.db_conf import get_database
from services.vector_store import vector_manager
from models.news import Category, News
from config.llm_conf import (
    LLM_MODEL,
    get_chat_model_kwargs,
)

# 导入你的缓存函数（use_rag=True 走 RAG 专用 db 15）
from cache.redis_cache import get_json_cache, set_cache

logger = logging.getLogger(__name__)

# 这些词是用户常用的分类说法。分类名称仍以数据库为准，别名只用于提升匹配成功率。
CATEGORY_ALIASES = {
    "头条": ("头条",),
    "社会": ("社会",),
    "国内": ("国内",),
    "国际": ("国际",),
    "娱乐": ("娱乐",),
    "体育": ("体育",),
    "科技": ("科技", "技术", "人工智能", "机器人", "芯片"),
    "财经": ("财经", "金融", "经济"),
}


class NewsRAG:
    def __init__(self, enable_cache: bool = True):
        self.llm = ChatOpenAI(**get_chat_model_kwargs())
        self.retriever = vector_manager.get_retriever(k=4)
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=True,
            chain_type="stuff"
        )
        self.enable_cache = enable_cache  # ：是否使用缓存

    @staticmethod
    def _get_search_terms(question: str) -> list[str]:
        """提取关键词，避免整句 LIKE 导致中文问题无法命中。"""
        terms: list[str] = []
        for span in re.findall(
            r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9][A-Za-z0-9_-]{1,}",
            question.lower(),
        ):
            # 年份单独作为时间过滤条件，不参与普通文本匹配。
            if span.isdigit() and len(span) == 4:
                continue
            terms.append(span)
            if len(span) >= 4 and re.fullmatch(r"[\u4e00-\u9fff]+", span):
                # 保留四字、三字片段，覆盖“国家账本”“财政预算”等核心短语。
                terms.extend(span[i : i + 4] for i in range(len(span) - 3))
                terms.extend(span[i : i + 3] for i in range(len(span) - 2))

        stopwords = {
            "请问", "帮我", "请总结", "请介绍", "请概括", "请分析", "总结一下",
            "介绍一下", "新闻内容", "相关内容", "主要内容", "值得关注", "最近有哪些",
        }
        unique_terms = []
        for term in terms:
            if len(term) >= 2 and term not in stopwords and term not in unique_terms:
                unique_terms.append(term)
        return unique_terms[:30]

    @staticmethod
    def _get_year(question: str) -> int | None:
        """识别问题中的四位年份，用于限制新闻发布时间。"""
        match = re.search(r"(?:19|20)\d{2}", question)
        return int(match.group()) if match else None

    @staticmethod
    def _get_category_aliases(question: str) -> list[str]:
        """识别分类和常用分类别名，避免只依赖标题正文 LIKE。"""
        normalized = question.lower()
        return [
            category
            for category, aliases in CATEGORY_ALIASES.items()
            if any(alias.lower() in normalized for alias in aliases)
        ]

    async def _keyword_documents(self, question: str, limit: int = 4) -> list[Document]:
        """Retrieve news from MySQL when the remote embedding service is unavailable."""
        terms = self._get_search_terms(question)
        year = self._get_year(question)
        category_aliases = self._get_category_aliases(question)
        async for db in get_database():
            try:
                filters = []

                if year:
                    filters.extend([
                        News.publish_time >= datetime(year, 1, 1),
                        News.publish_time < datetime(year + 1, 1, 1),
                    ])

                if category_aliases:
                    category_result = await db.execute(select(Category))
                    categories = category_result.scalars().all()
                    category_ids = [
                        category.id
                        for category in categories
                        if any(
                            alias in category.name or category.name in alias
                            for alias in category_aliases
                        )
                    ]
                    if category_ids:
                        filters.append(News.category_id.in_(category_ids))

                # 已识别分类时，分类本身就是更可靠的匹配条件；否则再用标题/正文关键词。
                if terms and not category_aliases:
                    filters.append(or_(*[
                        or_(News.title.contains(term), News.content.contains(term))
                        for term in terms
                    ]))

                query = select(News)
                if filters:
                    query = query.where(*filters)
                query = query.order_by(News.publish_time.desc()).limit(limit)
                rows = (await db.execute(query)).scalars().all()
                return [
                    Document(
                        page_content=(
                            f"新闻ID：{news.id}\n"
                            f"发布时间：{news.publish_time.strftime('%Y-%m-%d') if news.publish_time else '未知'}\n"
                            f"标题：{news.title}\n"
                            f"内容：{(news.content or news.description or '')[:1800]}"
                        ),
                        metadata={"news_id": news.id},
                    )
                    for news in rows
                ]
            finally:
                await db.close()
            break
        return []

    async def _answer_with_documents(
        self,
        question: str,
        documents: list[Document],
        callbacks: list | None = None,
    ) -> dict:
        """Generate an answer from retrieved documents without a vector chain."""
        context = "\n\n".join(doc.page_content for doc in documents)
        prompt = (
            "你是新闻问答助手。请严格根据下面的新闻资料回答用户问题。"
            "资料不足时明确说明，不要编造。提到具体新闻时使用 Markdown 链接，"
            "格式为 [新闻标题](/news/新闻ID)。\n\n"
            f"新闻资料：\n{context}\n\n"
            f"用户问题：{question}"
        )
        result = await self.llm.ainvoke(
            prompt,
            config={"callbacks": callbacks} if callbacks else None,
        )
        answer = result.content
        if isinstance(answer, list):
            answer = "".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in answer
            )
        return {
            "answer": answer,
            "source_news_ids": [doc.metadata["news_id"] for doc in documents],
            "retrieval_mode": "keyword",
        }

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

        # 有年份或分类限制时优先使用 SQL 精确过滤，避免向量检索跨年份、跨分类误召回。
        has_structured_filter = bool(
            self._get_year(question) or self._get_category_aliases(question)
        )
        if has_structured_filter:
            documents = await self._keyword_documents(question)
            if not documents:
                response = {
                    "answer": "暂时没有找到符合年份或分类条件的新闻内容。",
                    "source_news_ids": [],
                    "retrieval_mode": "keyword",
                }
            else:
                response = await self._answer_with_documents(
                    question,
                    documents,
                    callbacks=callbacks,
                )
            if self.enable_cache:
                await set_cache(cache_key, response, expire=3600, use_rag=True)
            return response

        # 无结构化限制时，继续使用向量检索；同步 Chroma 调用放到线程池，避免阻塞事件循环。
        try:
            vector_count = vector_manager.store._collection.count()
            if vector_count == 0:
                raise RuntimeError("vector collection is empty")

            loop = asyncio.get_event_loop()
            invoke = lambda q: self.qa_chain.invoke(
                q,
                config={"callbacks": callbacks} if callbacks else None,
            )
            result = await loop.run_in_executor(None, invoke, question)
            response = {
                "answer": result["result"],
                "source_news_ids": [
                    doc.metadata["news_id"] for doc in result["source_documents"]
                ],
                "retrieval_mode": "vector",
            }
        except Exception as vector_error:
            logger.warning(
                "Vector RAG unavailable, using keyword fallback: %s",
                vector_error,
            )
            documents = await self._keyword_documents(question)
            if not documents:
                response = {
                    "answer": "暂时没有找到与问题相关的新闻内容。",
                    "source_news_ids": [],
                    "retrieval_mode": "keyword",
                }
            else:
                response = await self._answer_with_documents(
                    question,
                    documents,
                    callbacks=callbacks,
                )

        # 3. 保存到缓存（新增）
        if self.enable_cache:
            await set_cache(cache_key, response, expire=3600, use_rag=True)
            print(f"💾 已缓存: {question[:50]}...")

        return response


#  生产环境使用 - 有缓存
rag = NewsRAG(enable_cache=True)

# 调试时使用 - 无缓存，每次都重新生成
rag_no_cache = NewsRAG(enable_cache=False)













