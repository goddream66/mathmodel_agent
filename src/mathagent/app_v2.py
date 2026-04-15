from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agents import ManagerAgent
from .chat_v2 import interactive_chat
from .io import load_problem_text, load_supporting_data
from .memory import MemoryStore
from .reporting import resolve_report_sections, select_report_sections
from .tools import ToolRegistry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mathagent")
    parser.add_argument("--problem-file", type=str, default=None)
    parser.add_argument("--db-path", type=str, default="data/mathagent.db")
    parser.add_argument(
        "--ocr",
        dest="ocr",
        action="store_true",
        help="Force OCR for images inside PDF files.",
    )
    parser.add_argument(
        "--no-ocr",
        dest="ocr",
        action="store_false",
        help="Disable automatic OCR for PDF files.",
    )
    parser.set_defaults(ocr=None)
    parser.add_argument(
        "--ocr-mode",
        type=str,
        default="auto",
        choices=["auto", "images", "page"],
        help="OCR mode: auto extracts images first, images scans only images, page scans whole pages.",
    )
    parser.add_argument("--out-dir", type=str, default="outputs")
    parser.add_argument("--chat", action="store_true", help="Start interactive multi-turn chat mode.")
    parser.add_argument(
        "--data-file",
        action="append",
        default=[],
        help="Attach a CSV, JSON, or XLSX data file. Repeat this flag for multiple files.",
    )
    parser.add_argument(
        "--report-section",
        action="append",
        default=[],
        help="Export only selected report sections, for example --report-section abstract --report-section results.",
    )
    args = parser.parse_args(argv)

    try:
        report_sections = resolve_report_sections(args.report_section)
    except ValueError as exc:
        print(str(exc))
        return 2

    tools = ToolRegistry.with_defaults(out_dir=args.out_dir)
    if args.chat:
        return interactive_chat(tools=tools, db_path=args.db_path, out_dir=args.out_dir)

    if args.problem_file:
        try:
            problem_text = load_problem_text(
                args.problem_file,
                enable_ocr=args.ocr,
                ocr_mode=args.ocr_mode,
            )
        except RuntimeError as exc:
            print(str(exc))
            return 2
    else:
        problem_text = "Paste your mathematical modeling problem here, or use --problem-file."

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "problem_text.md").write_text(problem_text, encoding="utf-8")
    supporting_data = load_supporting_data(args.data_file) if args.data_file else {}
    if supporting_data:
        (out_dir / "supporting_data.json").write_text(
            json.dumps(supporting_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    memory = MemoryStore(db_path=Path(args.db_path))
    manager = ManagerAgent()
    state = manager.run(
        problem_text=problem_text,
        tools=tools,
        memory=memory,
        input_data=supporting_data,
    )

    print("== Clarifications ==")
    for question in state.clarifications:
        print("-", question)
    print()

    print("== Solver Runs ==")
    for run in state.solver_runs:
        print("-", run.subproblem_title, "success" if run.success else "failed")
    print()

    print("== Report (Markdown) ==")
    rendered_report = select_report_sections(state.report_md or "", report_sections)
    print(rendered_report)
    if state.report_md:
        report_path = out_dir / "report.md"
        report_path.write_text(state.report_md, encoding="utf-8")
        print()
        print("== Saved ==")
        print(f"- {report_path}")
        if report_sections:
            selected_path = out_dir / "report_selected.md"
            selected_path.write_text(rendered_report, encoding="utf-8")
            print(f"- {selected_path}")
    return 0
