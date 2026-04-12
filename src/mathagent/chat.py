from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .agents import ManagerAgent
from .memory import MemoryStore
from .state import ConversationTurn, TaskState
from .tools import ToolRegistry


def _build_problem_text(turns: list[ConversationTurn]) -> str:
    user_messages = [turn.content.strip() for turn in turns if turn.role == "user" and turn.content.strip()]
    if not user_messages:
        return ""
    if len(user_messages) == 1:
        return user_messages[0]
    lines = ["初始题目与需求：", user_messages[0], "", "补充澄清与新增要求："]
    for index, message in enumerate(user_messages[1:], start=1):
        lines.append(f"{index}. {message}")
    return "\n".join(lines)


@dataclass
class ChatSession:
    tools: ToolRegistry
    db_path: Path
    out_dir: Path
    turns: list[ConversationTurn] = field(default_factory=list)
    latest_state: TaskState | None = None

    def add_user_message(self, content: str) -> None:
        self.turns.append(ConversationTurn(role="user", content=content.strip()))

    def reset(self) -> None:
        self.turns.clear()
        self.latest_state = None

    def generate(self) -> TaskState:
        problem_text = _build_problem_text(self.turns)
        memory = MemoryStore(db_path=self.db_path)
        state = ManagerAgent().run(problem_text=problem_text, tools=self.tools, memory=memory)
        state.conversation = list(self.turns)
        self.latest_state = state
        self._persist_outputs(state)
        return state

    def _persist_outputs(self, state: TaskState) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        transcript_lines: list[str] = []
        for turn in self.turns:
            transcript_lines.append(f"## {turn.role}")
            transcript_lines.append(turn.content)
            transcript_lines.append("")
        (self.out_dir / "chat_transcript.md").write_text("\n".join(transcript_lines), encoding="utf-8")
        if state.report_md:
            (self.out_dir / "chat_report.md").write_text(state.report_md, encoding="utf-8")


def interactive_chat(*, tools: ToolRegistry, db_path: str, out_dir: str) -> int:
    session = ChatSession(tools=tools, db_path=Path(db_path), out_dir=Path(out_dir))
    print("MathAgent chat mode")
    print("输入题目、补充条件或修改要求。")
    print("命令：/run 生成最新分析与论文草稿，/report 查看最新报告，/status 查看状态，/reset 重置，/exit 退出。")

    while True:
        try:
            user_input = input("you> ").strip()
        except EOFError:
            print()
            break

        if not user_input:
            continue
        if user_input == "/exit":
            break
        if user_input == "/reset":
            session.reset()
            print("assistant> 会话已重置，可以重新输入题目。")
            continue
        if user_input == "/status":
            if session.latest_state is None:
                print(f"assistant> 当前已记录 {len(session.turns)} 轮用户输入，还没有生成报告。")
            else:
                print(
                    "assistant> "
                    f"已记录 {len(session.turns)} 轮输入，"
                    f"拆出了 {len(session.latest_state.subproblems)} 个子问题，"
                    f"审稿提示 {len(session.latest_state.results.get('review_findings', []))} 条。"
                )
            continue
        if user_input == "/report":
            if session.latest_state is None or not session.latest_state.report_md:
                print("assistant> 还没有最新报告，先输入 /run。")
            else:
                print(session.latest_state.report_md)
            continue
        if user_input == "/run":
            if not session.turns:
                print("assistant> 还没有题目信息，请先输入题目或要求。")
                continue
            state = session.generate()
            print(
                "assistant> "
                f"已完成一轮生成：{len(state.subproblems)} 个子问题，"
                f"{len(state.solver_runs)} 次求解运行，"
                f"{len(state.results.get('review_findings', []))} 条审稿提示。"
            )
            print(f"assistant> 报告已保存到 {Path(out_dir) / 'chat_report.md'}")
            continue

        session.add_user_message(user_input)
        print("assistant> 已记录这轮输入。你可以继续补充约束、数据、目标，或输入 /run 生成最新论文草稿。")

    return 0
