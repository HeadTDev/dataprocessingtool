from dataclasses import dataclass


@dataclass(slots=True)
class MerkantilResult:
    cancelled: bool
    output_csv: str | None
    vehicle_count: int = 0
