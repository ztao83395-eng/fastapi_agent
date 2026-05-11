import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_conf import async_engine
from config.llm_conf import BAILIAN_API_KEY, EMBEDDING_MODEL, VECTOR_STORE_DIR
from models.news import News
from langchain_community import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
import aiohttp
import asyncio


async def build_news_vectors_optimized():
    async with AsyncSession(async_engine) as session:
        stmt = select(News)
        result = await session.execute(stmt)
        news_list = result.scalars().all()

        print(f"查询到 {len(news_list)} 条新闻")

        texts = []
        metadatas = []
        for news in news_list:
            title = news.title or ""
            content = news.content or ""
            text_content = f"{title}\n{content}".strip()

            if text_content:
                texts.append(text_content)
                metadatas.append({
                    "news_id": news.id,
                    "title": title,
                    "category_id": news.category_id,
                    "publish_time": str(news.publish_time) if news.publish_time else None,
                    "author": news.author or ""
                })

        print(f"有效文本: {len(texts)} 条")

        if not texts:
            return

        # 使用原生 dashscope 配置超时
        import dashscope
        dashscope.api_key = BAILIAN_API_KEY

        # 配置超时
        from dashscope import TextEmbedding

        embeddings = DashScopeEmbeddings(
            model=EMBEDDING_MODEL,
            dashscope_api_key=BAILIAN_API_KEY,
        )

        # 测试
        print("测试 embedding...")
        test_result = embeddings.embed_query("测试文本")
        print(f"测试成功，向量维度: {len(test_result)}")

        # 分批处理
        batch_size = 10
        total_batches = (len(texts) + batch_size - 1) // batch_size

        print(f"开始分批向量化，共 {total_batches} 批")

        first_batch = True

        for i in range(0, len(texts), batch_size):
            batch_num = i // batch_size + 1
            batch_texts = texts[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]

            print(f"处理第 {batch_num}/{total_batches} 批 ({len(batch_texts)} 条)...")

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if first_batch:
                        vectorstore = Chroma.from_texts(
                            texts=batch_texts,
                            embedding=embeddings,
                            metadatas=batch_metadatas,
                            persist_directory=VECTOR_STORE_DIR,
                        )
                        first_batch = False
                    else:
                        vectorstore.add_texts(
                            texts=batch_texts,
                            metadatas=batch_metadatas,
                        )
                    print(f"✅ 完成")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 10 * (attempt + 1)
                        print(f"⚠️ 失败，{wait_time}秒后重试...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"❌ 失败: {e}")

            # 批次间隔
            await asyncio.sleep(2)

        print(f"\n✅ 完成！")


if __name__ == "__main__":
    """
    运行检验
    asyncio.run(build_news_vectors_optimized())
    """

    #查看数据库信息
    embeddings = DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        dashscope_api_key=BAILIAN_API_KEY,
    )

    vectorstore = Chroma(
        persist_directory=VECTOR_STORE_DIR,
        embedding_function=embeddings
    )

    # 查看所有文档（需要先获取 collection）
    retriever = vectorstore.as_retriever()
    collection_data = vectorstore.get()
    print(collection_data)  # 包含 ids, documents, metadatas