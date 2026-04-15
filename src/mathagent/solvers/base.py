from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


SolverBuilder = Callable[[dict[str, Any]], tuple[str, str]]
SolverMatcher = Callable[[dict[str, Any]], float]


@dataclass(frozen=True)
class SolverSpec:
    name: str
    matcher: SolverMatcher
    builder: SolverBuilder
    description: str = ""


@dataclass(frozen=True)
class SolverSelection:
    name: str
    summary: str
    code: str
    score: float


class SolverRegistry:
    def __init__(self) -> None:
        self._specs: list[SolverSpec] = []

    def register(self, spec: SolverSpec) -> None:
        self._specs.append(spec)

    def list_names(self) -> list[str]:
        return [spec.name for spec in self._specs]

    def select(self, context: dict[str, Any]) -> SolverSelection | None:
        best_spec: SolverSpec | None = None
        best_score = float("-inf")
        for spec in self._specs:
            score = float(spec.matcher(context))
            if score <= 0:
                continue
            if score > best_score:
                best_spec = spec
                best_score = score
        if best_spec is None:
            return None
        summary, code = best_spec.builder(context)
        return SolverSelection(
            name=best_spec.name,
            summary=summary,
            code=code,
            score=best_score,
        )
