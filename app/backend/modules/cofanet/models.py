from dataclasses import dataclass


@dataclass(slots=True)
class CofanetResult:
    cancelled: bool
    rows_count: int
    vevok_csv_path: str | None
    coface_output_path: str | None
