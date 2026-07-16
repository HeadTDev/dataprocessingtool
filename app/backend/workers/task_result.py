from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TaskResult:
    success: bool
    cancelled: bool = False
    output_path: str | None = None
    summary: str = ""
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
