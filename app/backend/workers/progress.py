from dataclasses import dataclass


@dataclass(slots=True)
class ProgressUpdate:
    message: str = ""
    current: int = 0
    total: int = 0
    indeterminate: bool = False
