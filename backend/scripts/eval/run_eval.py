"""Agent 评测入口

用法（在项目根目录）：
  python -m backend.scripts.eval.run_eval                        # 跑全部评测
  python -m backend.scripts.eval.run_eval --rag --limit 5        # 只跑 RAG，前 5 条
  python -m backend.scripts.eval.run_eval --agent                # 只跑 Agent
  python -m backend.scripts.eval.run_eval --generate 10          # 从新闻库自动生成评测集
  python -m backend.scripts.eval.run_eval --output docs/eval_report.md --judge-model gpt-5.6-luna

依赖：GPT_API_KEY 或 OPENAI_API_KEY（对话、Agent、评测和 embedding）、MySQL、向量库已构建（scripts/build_vectors.py）
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# 评测脚本统一使用 backend 作为 Python 模块根目录。
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scripts.eval.dataset import load_dataset, generate_rag_questions, DEFAULT_DATASET
from scripts.eval.judge import Judge
from scripts.eval.rag_eval import run_rag_eval
from scripts.eval.agent_eval import run_agent_eval

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("run_eval")


def format_report(rag_results: list[dict], agent_results: list[dict]) -> str:
    """生成 Markdown 评测报告"""
    lines = ["# Agent 评测报告", ""]
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    def avg(results, metric):
        scores = [r["scores"].get(metric) for r in results if r.get("scores") and r["scores"].get(metric) is not None]
        return round(sum(scores) / len(scores), 2) if scores else "-"

    # ---- RAG 汇总 ----
    if rag_results:
        lines.append("## RAG 问答质量")
        lines.append("")
        lines.append("| 指标 | 平均分 (0-5) |")
        lines.append("|---|---|")
        for m, label in [("faithfulness", "忠实度"), ("context_relevance", "上下文相关性"), ("answer_relevance", "答案相关性")]:
            lines.append(f"| {label} | {avg(rag_results, m)} |")
        lines.append("")
        lines.append("### 用例明细")
        lines.append("")
        for r in rag_results:
            if r.get("error"):
                lines.append(f"- ❌ **{r['question'][:50]}** — 失败: {r['error']}")
                continue
            f, c, a = r["scores"].get("faithfulness", "-"), r["scores"].get("context_relevance", "-"), r["scores"].get("answer_relevance", "-")
            lines.append(f"- {'✅' if isinstance(f, (int, float)) and f >= 4 else '⚠️'} **{r['question'][:50]}** — 忠实度 {f} | 上下文 {c} | 答案 {a}（检索 {r.get('source_count', 0)} 条）")
        lines.append("")

    # ---- Agent 汇总 ----
    if agent_results:
        lines.append("## Agent 工具调用")
        lines.append("")
        lines.append("| 指标 | 平均分 (0-5) |")
        lines.append("|---|---|")
        for m, label in [("tool_correctness", "工具调用正确性"), ("intent_satisfaction", "意图满足度")]:
            lines.append(f"| {label} | {avg(agent_results, m)} |")
        lines.append("")
        lines.append("### 用例明细")
        lines.append("")
        for r in agent_results:
            if r.get("error"):
                lines.append(f"- ❌ **{r['question'][:50]}** — 失败: {r['error']}")
                continue
            t, i = r["scores"].get("tool_correctness", "-"), r["scores"].get("intent_satisfaction", "-")
            calls = " → ".join(c["tool"] for c in r.get("tool_calls", [])) or "无"
            lines.append(f"- {'✅' if isinstance(t, (int, float)) and t >= 4 else '⚠️'} **{r['question'][:50]}** — 工具 {t} | 意图 {i}（调用: {calls}）")
            if t == 0 or i < 3:
                lines.append(f"  - 工具原因: {r['reasons'].get('tool_correctness', '')}")
                lines.append(f"  - 意图原因: {r['reasons'].get('intent_satisfaction', '')}")
        lines.append("")

    lines.append("## 结论")
    lines.append("")
    lines.append("- 指标 < 3 分的部分建议针对性优化：检索质量差 → 检查向量库/embedding；忠实度低 → 检查提示词与上下文截断。")
    return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description="新闻 Agent 评测")
    parser.add_argument("--rag", action="store_true", help="运行 RAG 评测")
    parser.add_argument("--agent", action="store_true", help="运行 Agent 评测")
    parser.add_argument("--limit", type=int, default=None, help="每个评测最多跑 N 条")
    parser.add_argument("--generate", type=int, default=0, metavar="N", help="从新闻库生成 N 条 RAG 评测项")
    parser.add_argument("--dataset", type=str, default=str(DEFAULT_DATASET), help="评测集路径")
    parser.add_argument("--output", type=str, default="docs/eval_report.md", help="报告输出路径")
    parser.add_argument("--judge-model", type=str, default=None, help="判定模型（默认同 LLM_MODEL）")
    args = parser.parse_args()

    if args.generate:
        count = await generate_rag_questions(args.generate, Path(args.dataset))
        logger.info("生成完成，新增 %d 条", len(count))
        return

    if not (args.rag or args.agent):
        args.rag = args.agent = True

    judge = Judge(model=args.judge_model)
    data = load_dataset(Path(args.dataset))

    rag_results, agent_results = [], []
    if args.rag:
        rag_results = await run_rag_eval(judge, data.get("rag_questions", []), args.limit)
    if args.agent:
        agent_results = await run_agent_eval(judge, data.get("agent_tasks", []), args.limit)

    report = format_report(rag_results, agent_results)
    out = Path(args.output)
    out.write_text(report, encoding="utf-8")
    print(report)
    logger.info("报告已保存: %s", out.resolve())
    # 关闭连接池，避免退出时报 "Event loop is closed"
    from config.db_conf import async_engine
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
