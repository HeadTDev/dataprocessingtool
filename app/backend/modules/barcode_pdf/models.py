from dataclasses import dataclass, field


@dataclass(slots=True)
class BarcodeCopyResult:
    copied_count: int = 0
    missing_count: int = 0
    missing_barcodes: list[str] = field(default_factory=list)
    cancelled: bool = False
