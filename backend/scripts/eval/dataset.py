"""评测集：加载 JSON 评测集 / 从新闻库自动生成评测集"""
import asyncio
import json
import logging
import re
from pathlib import Path

from sqlalchemy import select, func

from config.db_conf import AsyncSessionLocal
from config.llm_conf import get_chat_model_kwargs
from models.news import News
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

DEFAULT_DATASET = Path(__file__).parent / "dataset.json"


def load_dataset(path: Path | None = None) -> dict:
    """加载评测集，返回 {rag_questions: [...], agent_tasks: [...]}"""
    p = Path(path) if path else DEFAULT_DATASET
    if not p.exists():
        return {"rag_questions": [], "agent_tasks": []}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_dataset(data: dict, path: Path | None = None):
    p = Path(path) if path else DEFAULT_DATASET
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def generate_rag_questions(count: int = 10, out: Path | None = None) -> list[dict]:
    """从新闻库随机抽新闻，用 LLM 基于新闻内容生成"问题 + 期望要点"。

    返回评测项列表，并保存到文件（默认 dataset.json，合并进 rag_questions）。
    """
    llm = ChatOpenAI(**get_chat_model_kwargs())

    # 随机抽样新闻
    async with AsyncSessionLocal() as db:
        total = (await db.execute(select(func.count(News.id)))).scalar()
        if total == 0:
            logger.error("新闻库为空，请先导入新闻数据")
            return []
        ids = (await db.execute(
            select(News.id).order_by(func.rand()).limit(min(count * 3, total))
        )).scalars().all()
        # 每个问题用一条新闻作为依据，抽样后截取
        sample_ids = ids[:count]
        rows = (await db.execute(select(News).where(News.id.in_(sample_ids)))).scalars().all()

    items = []
    for news in rows:
        content = (news.content or news.description or "")[:500]
        prompt = f"""你是新闻评测集设计师。基于下面这条新闻，设计一个用户可以问新闻 Agent 的问题。
要求：问题有明确答案、不能直接抄标题、符合真实用户提问习惯。

新闻标题：{news.title}
新闻内容：{content}

只输出 JSON：{{"question": "用户问题", "expected_points": ["答案应包含的要点1", "要点2"]}}
"""
        try:
            resp = await llm.ainvoke(prompt)
            m = re.search(r"\{.*\}", resp.content, re.DOTALL)
            if not m:
                logger.warning("生成失败（无 JSON）: %s", news.title)
                continue
            item = json.loads(m.group(0))
            item["reference_news_ids"] = [news.id]
            items.append(item)
            logger.info("已生成: %s", item["question"][:40])
        except Exception as e:
            logger.warning("生成失败: %s", e)

    # 合并保存
    data = load_dataset(out)
    existing = {q["question"] for q in data["rag_questions"]}
    new_items = [i for i in items if i["question"] not in existing]
    data["rag_questions"].extend(new_items)
    save_dataset(data, out)
    logger.info("新增 %d 条 RAG 评测项，共 %d 条", len(new_items), len(data["rag_questions"]))
    return new_items
