from __future__ import annotations

import argparse
from pathlib import Path

from .agents import ManagerAgent
from .io import load_problem_text
from .memory import MemoryStore
from .tools import ToolRegistry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mathagent")
    parser.add_argument("--problem-file", type=str, default=None)
    parser.add_argument("--db-path", type=str, default="data/mathagent.db")
    parser.add_argument("--ocr", action="store_true", help="对 PDF 内图片做 OCR（需要额外安装依赖）")
    parser.add_argument(
        "--ocr-mode",
        type=str,
        default="auto",
        choices=["auto", "images", "page"],
        help="OCR 模式：auto=优先抽取页内图片，抽不到则整页OCR；images=只做页内图片；page=直接整页OCR",
    )
    parser.add_argument("--out-dir", type=str, default="outputs")
    args = parser.parse_args(argv)

    if args.problem_file:
        try:
            problem_text = load_problem_text(
                args.problem_file, enable_ocr=args.ocr, ocr_mode=args.ocr_mode
            )
        except RuntimeError as e:
            print(str(e))
            return 2
    else:
        problem_text = "请把你的题目粘贴到这里（这是框架骨架的默认示例题目）。"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "problem_text.md").write_text(problem_text, encoding="utf-8")

    tools = ToolRegistry.empty()
    memory = MemoryStore(db_path=Path(args.db_path))
    manager = ManagerAgent()
    state = manager.run(problem_text=problem_text, tools=tools, memory=memory)

    print("== Clarifications ==")
    for q in state.clarifications:
        print("-", q)
    print()

    print("== Report (Markdown) ==")
    print(state.report_md or "")
    if state.report_md:
        (out_dir / "report.md").write_text(state.report_md, encoding="utf-8")
        print()
        print(f"== Saved ==")
        print(f"- {out_dir / 'report.md'}")
    return 0
