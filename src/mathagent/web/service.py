from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Literal
from uuid import uuid4

from ..orchestrator import Orchestrator
from ..reporting import available_report_sections, resolve_report_sections, select_report_sections
from ..state import TaskState
from ..tools import ToolRegistry
from ..io import load_problem_text, load_supporting_data

UploadRole = Literal["problem", "data"]


@dataclass
class UploadedFile:
    role: UploadRole
    name: str
    path: Path
    created_at: str


@dataclass
class WebSession:
    session_id: str
    created_at: str
    root_dir: Path
    messages: list[str] = field(default_factory=list)
    problem_files: list[UploadedFile] = field(default_factory=list)
    data_files: list[UploadedFile] = field(default_factory=list)
    selected_sections: list[str] = field(default_factory=list)
    latest_state: TaskState | None = None
    latest_report_md: str = ""


class WebSessionService:
    def __init__(self, *, root_dir: str | Path = "outputs/web_sessions") -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, WebSession] = {}
        self._lock = Lock()

    def available_sections(self) -> list[dict[str, str]]:
        return available_report_sections()

    def create_session(self) -> dict[str, Any]:
        session_id = uuid4().hex
        session_root = self.root_dir / session_id
        session_root.mkdir(parents=True, exist_ok=False)
        (session_root / "problem").mkdir(parents=True, exist_ok=True)
        (session_root / "data").mkdir(parents=True, exist_ok=True)
        (session_root / "outputs").mkdir(parents=True, exist_ok=True)

        session = WebSession(
            session_id=session_id,
            created_at=_now_iso(),
            root_dir=session_root,
        )
        with self._lock:
            self._sessions[session_id] = session
        self._persist_manifest(session)
        return self.get_session_summary(session_id)

    def add_message(self, session_id: str, content: str) -> dict[str, Any]:
        session = self._require_session(session_id)
        clean = content.strip()
        if not clean:
            raise ValueError("Message content cannot be empty.")
        session.messages.append(clean)
        self._persist_transcript(session)
        self._persist_manifest(session)
        return self.get_session_summary(session_id)

    def upload_files(
        self,
        session_id: str,
        role: UploadRole,
        files: list[tuple[str, bytes]],
    ) -> dict[str, Any]:
        session = self._require_session(session_id)
        if role not in {"problem", "data"}:
            raise ValueError("File role must be 'problem' or 'data'.")
        if not files:
            raise ValueError("No files were provided.")

        saved_files: list[UploadedFile] = []
        target_dir = session.root_dir / role
        for original_name, content in files:
            safe_name = Path(original_name).name or f"{role}_{uuid4().hex[:8]}"
            stored_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}_{safe_name}"
            stored_path = target_dir / stored_name
            stored_path.write_bytes(content)
            saved_files.append(
                UploadedFile(
                    role=role,
                    name=safe_name,
                    path=stored_path,
                    created_at=_now_iso(),
                )
            )

        if role == "problem":
            session.problem_files = saved_files
        else:
            session.data_files.extend(saved_files)

        self._persist_manifest(session)
        return self.get_session_summary(session_id)

    def set_report_sections(self, session_id: str, sections: list[str]) -> dict[str, Any]:
        session = self._require_session(session_id)
        session.selected_sections = resolve_report_sections(sections)
        self._persist_manifest(session)
        return self.get_session_summary(session_id)

    def run_session(self, session_id: str, *, sections: list[str] | None = None) -> dict[str, Any]:
        session = self._require_session(session_id)
        if sections is not None:
            session.selected_sections = resolve_report_sections(sections)

        problem_text = self._build_problem_text(session)
        if not problem_text.strip():
            raise ValueError("Please enter a problem statement or upload a problem file before running.")

        input_data = (
            load_supporting_data([file.path for file in session.data_files])
            if session.data_files
            else {}
        )
        out_dir = session.root_dir / "outputs"
        tools = ToolRegistry.with_defaults(out_dir=out_dir)
        state = Orchestrator(tools=tools).run(problem_text, input_data=input_data)

        session.latest_state = state
        session.latest_report_md = state.report_md or ""
        self._persist_run_outputs(session, input_data=input_data)
        self._persist_manifest(session)
        return self._build_run_payload(session)

    def get_report(self, session_id: str, *, sections: list[str] | None = None) -> dict[str, Any]:
        session = self._require_session(session_id)
        report_md = session.latest_report_md
        requested_sections = (
            resolve_report_sections(sections)
            if sections is not None
            else session.selected_sections
        )
        selected_report = select_report_sections(report_md, requested_sections)
        return {
            "session_id": session.session_id,
            "sections": requested_sections,
            "report_md": report_md,
            "selected_report_md": selected_report,
        }

    def get_session_summary(self, session_id: str) -> dict[str, Any]:
        session = self._require_session(session_id)
        return self._serialize_session(session)

    def _build_problem_text(self, session: WebSession) -> str:
        parts: list[str] = []
        if session.problem_files:
            latest_problem = session.problem_files[-1]
            parts.append(load_problem_text(latest_problem.path))

        messages = [message.strip() for message in session.messages if message.strip()]
        if messages:
            if len(messages) == 1:
                parts.append(messages[0])
            else:
                lines = ["补充要求与多轮澄清："]
                for index, message in enumerate(messages, start=1):
                    lines.append(f"{index}. {message}")
                parts.append("\n".join(lines))

        return "\n\n".join([part.strip() for part in parts if part.strip()]).strip()

    def _persist_transcript(self, session: WebSession) -> None:
        transcript_path = session.root_dir / "messages.md"
        lines = ["# Session Messages", ""]
        for index, message in enumerate(session.messages, start=1):
            lines.append(f"## User Message {index}")
            lines.append(message)
            lines.append("")
        transcript_path.write_text("\n".join(lines), encoding="utf-8")

    def _persist_manifest(self, session: WebSession) -> None:
        payload = self._serialize_session(session)
        (session.root_dir / "session.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _persist_run_outputs(self, session: WebSession, *, input_data: dict[str, Any]) -> None:
        outputs_dir = session.root_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        if session.latest_report_md:
            (outputs_dir / "report.md").write_text(session.latest_report_md, encoding="utf-8")
            if session.selected_sections:
                selected = select_report_sections(session.latest_report_md, session.selected_sections)
                (outputs_dir / "report_selected.md").write_text(selected, encoding="utf-8")
        if input_data:
            (outputs_dir / "supporting_data.json").write_text(
                json.dumps(input_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if session.latest_state is not None:
            (outputs_dir / "state_snapshot.json").write_text(
                json.dumps(self._serialize_task_state(session.latest_state), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def _build_run_payload(self, session: WebSession) -> dict[str, Any]:
        report = self.get_report(session.session_id)
        payload = self._serialize_session(session)
        payload["report"] = report
        return payload

    def _serialize_session(self, session: WebSession) -> dict[str, Any]:
        return {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "messages": list(session.messages),
            "problem_files": [_serialize_upload(file) for file in session.problem_files],
            "data_files": [_serialize_upload(file) for file in session.data_files],
            "selected_sections": list(session.selected_sections),
            "latest_state": self._serialize_task_state(session.latest_state) if session.latest_state else None,
            "report_ready": bool(session.latest_report_md.strip()),
        }

    def _serialize_task_state(self, state: TaskState | None) -> dict[str, Any] | None:
        if state is None:
            return None
        return {
            "stage": state.stage,
            "clarifications": list(state.clarifications),
            "subproblem_count": len(state.subproblems),
            "subproblems": [
                {
                    "title": subproblem.title,
                    "objective": subproblem.analysis.objective,
                    "chosen_method": subproblem.analysis.chosen_method,
                    "task_types": list(subproblem.analysis.task_types),
                }
                for subproblem in state.subproblems
            ],
            "solver_run_count": len(state.solver_runs),
            "solver_runs": [
                {
                    "subproblem_title": run.subproblem_title,
                    "success": run.success,
                    "schema_valid": run.schema_valid,
                    "summary": run.summary,
                    "structured_result": run.structured_result,
                    "artifacts": list(run.artifacts),
                }
                for run in state.solver_runs
            ],
            "results": {
                "status": state.results.get("status"),
                "solver_summary": state.results.get("solver_summary"),
                "review_findings": state.results.get("review_findings", []),
                "solved_subproblems": state.results.get("solved_subproblems", []),
                "partial_subproblems": state.results.get("partial_subproblems", []),
            },
        }

    def _require_session(self, session_id: str) -> WebSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Unknown session: {session_id}")
        return session


def _serialize_upload(file: UploadedFile) -> dict[str, str]:
    return {
        "role": file.role,
        "name": file.name,
        "path": str(file.path),
        "created_at": file.created_at,
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
