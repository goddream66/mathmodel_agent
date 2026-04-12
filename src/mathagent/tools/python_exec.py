from __future__ import annotations

import json
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PythonExecTool:
    name: str = "python_exec"
    description: str = "Execute generated Python code in an isolated run directory."
    work_dir: Path = Path("outputs/tool_runs")
    timeout_s: float = 20.0

    def run(self, input: Any) -> dict[str, Any]:
        if not isinstance(input, dict):
            raise TypeError("python_exec input must be a dict")

        code = str(input.get("code") or "").strip()
        if not code:
            raise ValueError("python_exec requires non-empty 'code'")

        timeout_s = float(input.get("timeout_s") or self.timeout_s)
        filename = str(input.get("filename") or "solver.py")
        context = input.get("context")

        run_dir = self._create_run_dir()
        script_path = run_dir / filename
        script_path.write_text(code, encoding="utf-8")

        if context is not None:
            (run_dir / "context.json").write_text(
                json.dumps(context, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        before_files = {p.relative_to(run_dir).as_posix() for p in run_dir.rglob("*") if p.is_file()}
        try:
            completed = subprocess.run(
                [sys.executable, script_path.name],
                cwd=run_dir,
                text=True,
                capture_output=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "success": False,
                "stdout": exc.stdout or "",
                "stderr": (exc.stderr or "") + f"\nTimed out after {timeout_s:.1f}s",
                "returncode": None,
                "run_dir": str(run_dir),
                "artifacts": self._collect_artifacts(run_dir, before_files),
            }

        return {
            "success": completed.returncode == 0,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
            "run_dir": str(run_dir),
            "artifacts": self._collect_artifacts(run_dir, before_files),
        }

    def _create_run_dir(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(self.work_dir) / f"run_{timestamp}_{uuid.uuid4().hex[:8]}"
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_dir

    def _collect_artifacts(self, run_dir: Path, before_files: set[str]) -> list[str]:
        artifacts: list[str] = []
        for path in sorted(p for p in run_dir.rglob("*") if p.is_file()):
            rel = path.relative_to(run_dir).as_posix()
            if rel not in before_files:
                artifacts.append(rel)
        return artifacts
