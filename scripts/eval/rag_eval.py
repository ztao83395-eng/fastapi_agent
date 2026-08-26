"""RAG 质量评测 —— 忠实度 / 上下文相关性 / 答案相关性

对评测集中每个问题：
1. 用 rag_no_cache 真实检索+回答（跳过缓存，force_refresh）
2. 按 source_news_ids 从数据库取回上下文
3. 三项指标打分
"""
import logging

from sqlalchemy import select

from config.db_conf import AsyncSessionLocal
from models.news import News
from services.rag_chain import rag_no_cache
from scripts.eval.judge import Judge, split_sentences

logger = logging.getLogger(__name__)


async def fetch_news_contents(news_ids: list[int]) -> str:
    """根据新闻 ID 从数据库取回内容，拼接成上下文"""
    if not news_ids:
        return ""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(News).where(News.id.in_(news_ids)))
        rows = result.scalars().all()
    parts = []
    for n in rows:
        parts.append(f"【新闻{n.id}】标题：{n.title}\n内容：{(n.content or n.description or '')[:400]}")
    return "\n".join(parts)


async def eval_one(judge: Judge, item: dict) -> dict:
    """评测单条 RAG 用例，返回结构化结果"""
    question = item["question"]
    result = {
        "question": question,
        "expected_points": item.get("expected_points", []),
        "scores": {},
        "reasons": {},
    }

    # 1. 真实跑一次 RAG（禁用缓存，保证评测可信）
    resp = await rag_no_cache.ask(question, force_refresh=True)
    answer = resp["answer"]
    source_ids = resp.get("source_news_ids", [])
    context = await fetch_news_contents(source_ids)
    result["answer"] = answer[:200]
    result["source_count"] = len(source_ids)

    # 2. 忠实度：逐句判定（最多 5 句），分数 = 支持句占比 × 5
    claims = split_sentences(answer, limit=5)
    if claims:
        supported = 0
        for claim in claims:
            s, reason = await judge.faithfulness_sentence(claim, context)
            supported += s
            result["reasons"].setdefault("faithfulness", []).append(f"{claim[:30]}… -> {'✓' if s else '✗'}")
        result["scores"]["faithfulness"] = round(supported / len(claims) * 5, 2)
    else:
        result["scores"]["faithfulness"] = 0.0

    # 3. 上下文相关性（检索质量）
    s, reason = await judge.context_relevance(question, context or "（检索结果为空）")
    result["scores"]["context_relevance"] = s
    result["reasons"]["context_relevance"] = reason

    # 4. 答案相关性（有没有答对题）
    s, reason = await judge.answer_relevance(question, answer)
    result["scores"]["answer_relevance"] = s
    result["reasons"]["answer_relevance"] = reason

    return result


async def run_rag_eval(judge: Judge, items: list[dict], limit: int | None = None) -> list[dict]:
    """跑完整 RAG 评测，返回每个用例的结果列表"""
    results = []
    for i, item in enumerate(items[:limit] if limit else items, 1):
        logger.info("[RAG %d/%d] %s", i, len(items), item["question"][:40])
        try:
            r = await eval_one(judge, item)
            avg = sum(r["scores"].values()) / len(r["scores"])
            logger.info("  avg=%.2f faithfulness=%.2f context=%.2f answer=%.2f",
                        avg, r["scores"]["faithfulness"], r["scores"]["context_relevance"], r["scores"]["answer_relevance"])
            results.append(r)
        except Exception as e:
            logger.error("用例失败: %s", e)
            results.append({"question": item["question"], "error": str(e), "scores": {}})
    return results
