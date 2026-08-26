"""LLM 判定器 —— 用 qwen-plus 对 RAG/Agent 输出进行打分

所有指标均输出 0-5 分（faithfulness 句子级输出 0/1），解析失败自动重试一次。
"""
import asyncio
import json
import re
import logging

from langchain_openai import ChatOpenAI
from config.llm_conf import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, TEMPERATURE

logger = logging.getLogger(__name__)


def split_sentences(text: str, limit: int = 5) -> list[str]:
    """按中文句号拆句，最多取前 limit 句"""
    parts = re.split(r"[。！？!?\n]", text)
    return [p.strip() for p in parts if p.strip()][:limit]


class Judge:
    """判定模型封装，所有方法返回 (score, reason)"""

    def __init__(self, model: str | None = None):
        self.llm = ChatOpenAI(
            openai_api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            model_name=model or LLM_MODEL,
            temperature=0,  # 判定要确定性，温度设 0
        )

    async def _ask_json(self, prompt: str, max_retry: int = 1) -> dict | None:
        """要求模型只输出 JSON，解析失败重试"""
        for _ in range(max_retry + 1):
            try:
                resp = await self.llm.ainvoke(prompt)
                text = resp.content
                # 提取 JSON 块（模型偶尔会包在 ```json ... ``` 里）
                m = re.search(r"\{.*\}", text, re.DOTALL)
                if not m:
                    continue
                return json.loads(m.group(0))
            except Exception as e:
                logger.warning("judge 解析失败: %s", e)
        return None

    # ============ 指标 1：忠实度（faithfulness）============
    async def faithfulness_sentence(self, claim: str, context: str) -> tuple[int, str]:
        """判定答案中的单句陈述是否被检索到的上下文支持"""
        prompt = f"""你是新闻问答评测员。判断下面这条"陈述"是否能由"上下文"直接支持或推断出来。
注意：上下文不支持、无法验证、或者陈述与上下文矛盾，都算不支持。

上下文：
{context[:1500]}

陈述：
{claim}

只输出 JSON：{{"supported": 0 或 1, "reason": "一句话说明"}}
"""
        data = await self._ask_json(prompt)
        if data is None:
            return (0, "judge 无输出")
        return (1 if data.get("supported") == 1 else 0, data.get("reason", ""))

    # ============ 指标 2：答案相关性（answer relevance）============
    async def answer_relevance(self, question: str, answer: str) -> tuple[int, str]:
        """判定答案是否直接回答了问题（不看上下文，只问答对题）"""
        prompt = f"""你是新闻问答评测员。判断答案是否直接、完整地回答了问题。
0 分：答非所问；5 分：完全切题且信息充足。

问题：{question}

答案：{answer[:800]}

只输出 JSON：{{"score": 0到5的整数, "reason": "一句话说明"}}
"""
        data = await self._ask_json(prompt)
        if data is None:
            return (0, "judge 无输出")
        try:
            return (int(data["score"]), data.get("reason", ""))
        except (KeyError, ValueError):
            return (0, "judge 输出格式错误")

    # ============ 指标 3：上下文相关性（context relevance）============
    async def context_relevance(self, question: str, context: str) -> tuple[int, str]:
        """判定检索到的上下文与问题相关程度（衡量检索质量）"""
        prompt = f"""你是新闻检索评测员。判断下面这段"检索结果"与问题的相关程度。
0 分：完全不相关；5 分：高度相关且包含回答问题所需信息。

问题：{question}

检索结果：
{context[:1500]}

只输出 JSON：{{"score": 0到5的整数, "reason": "一句话说明"}}
"""
        data = await self._ask_json(prompt)
        if data is None:
            return (0, "judge 无输出")
        try:
            return (int(data["score"]), data.get("reason", ""))
        except (KeyError, ValueError):
            return (0, "judge 输出格式错误")

    # ============ 指标 4：意图满足度（agent）============
    async def intent_satisfaction(self, question: str, tool_calls: list[str], answer: str) -> tuple[int, str]:
        """判定 Agent 的工具调用 + 最终回答整体上是否满足了用户意图"""
        calls = "、".join(tool_calls) if tool_calls else "（未调用任何工具）"
        prompt = f"""你是 Agent 评测员。用户提出了一个问题，Agent 调用了若干工具并给出最终回答。
判断整个流程是否成功满足了用户的意图。
0 分：完全失败；5 分：完美满足。

用户问题：{question}

Agent 调用的工具：{calls}

Agent 最终回答：{answer[:800]}

只输出 JSON：{{"score": 0到5的整数, "reason": "一句话说明"}}
"""
        data = await self._ask_json(prompt)
        if data is None:
            return (0, "judge 无输出")
        try:
            return (int(data["score"]), data.get("reason", ""))
        except (KeyError, ValueError):
            return (0, "judge 输出格式错误")
