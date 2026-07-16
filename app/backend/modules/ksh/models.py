from dataclasses import dataclass


@dataclass(slots=True)
class KshResult:
    cancelled: bool
    output_path: str | None
    row_count: int = 0
    cleanup_message: str = ""
