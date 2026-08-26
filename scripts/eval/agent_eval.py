"""Agent 工具调用评测

对评测集中每个任务：
1. 设置用户上下文（contextvar），真实跑 AgentExecutor
2. 从 intermediate_steps 提取工具调用序列，与期望工具/参数比对
3. judge 对整体意图满足度打分

评分规则（工具调用正确性，满分 5）：
- 期望工具被调用且参数匹配 → 5
- 期望工具被调用但参数不匹配 → 3
- 调用了工具但不是期望的 → 1
- 完全没调用工具 → 0
"""
import logging

from services.agent_tools import create_agent_executor
from services.context import current_user_id_var
from scripts.eval.judge import Judge

logger = logging.getLogger(__name__)

_executor = None


def get_executor():
    """评测用 AgentExecutor（懒加载，避免重复创建）"""
    global _executor
    if _executor is None:
        _executor = create_agent_executor()
    return _executor


def extract_tool_calls(result: dict) -> list[dict]:
    """从 AgentExecutor 结果中提取 (tool, tool_input) 序列"""
    calls = []
    for step in result.get("intermediate_steps", []):
        action, _ = step  # (AgentAction, observation)
        calls.append({"tool": action.tool, "args": action.tool_input})
    return calls


def score_tool_calls(calls: list[dict], expected_tool: str, expected_args: dict | None) -> tuple[float, str]:
    """按规则给工具调用打分"""
    matched = [c for c in calls if c["tool"] == expected_tool]
    if not matched:
        if calls:
            return 1.0, f"调用了工具 {[c['tool'] for c in calls]}，但期望 {expected_tool}"
        return 0.0, "未调用任何工具"
    if expected_args:
        actual = matched[-1]["args"]
        mismatches = {k: (v, actual.get(k)) for k, v in expected_args.items() if actual.get(k) != v}
        if mismatches:
            return 3.0, f"参数不匹配: {mismatches}"
    return 5.0, "工具调用正确"


async def eval_one(judge: Judge, item: dict) -> dict:
    """评测单条 Agent 任务"""
    question = item["question"]
    expected_tool = item.get("expected_tool")
    expected_args = item.get("expected_args")
    user_id = item.get("user_id", 1)
    result = {
        "question": question,
        "expected_tool": expected_tool,
        "expected_args": expected_args,
        "scores": {},
        "reasons": {},
    }

    # 设置用户上下文（评测完还原，避免污染其他用例）
    token = current_user_id_var.set(user_id)
    try:
        resp = await get_executor().ainvoke({"input": question})
    finally:
        current_user_id_var.reset(token)

    calls = extract_tool_calls(resp)
    result["tool_calls"] = calls
    result["answer"] = resp.get("output", "")[:200]

    # 1. 工具调用正确性
    if expected_tool:
        score, reason = score_tool_calls(calls, expected_tool, expected_args)
        result["scores"]["tool_correctness"] = score
        result["reasons"]["tool_correctness"] = reason
    else:
        result["scores"]["tool_correctness"] = 5.0 if calls else 0.0
        result["reasons"]["tool_correctness"] = "有调用" if calls else "无调用"

    # 2. 意图满足度（judge 综合打分）
    s, reason = await judge.intent_satisfaction(question, [c["tool"] for c in calls], result["answer"])
    result["scores"]["intent_satisfaction"] = s
    result["reasons"]["intent_satisfaction"] = reason

    return result


async def run_agent_eval(judge: Judge, items: list[dict], limit: int | None = None) -> list[dict]:
    results = []
    for i, item in enumerate(items[:limit] if limit else items, 1):
        logger.info("[AGENT %d/%d] %s", i, len(items), item["question"][:40])
        try:
            r = await eval_one(judge, item)
            logger.info("  tool=%.1f intent=%.1f calls=%s",
                        r["scores"]["tool_correctness"], r["scores"]["intent_satisfaction"],
                        [c["tool"] for c in r.get("tool_calls", [])])
            results.append(r)
        except Exception as e:
            logger.error("用例失败: %s", e)
            results.append({"question": item["question"], "error": str(e), "scores": {}})
    return results
