"""Limits and paths. Each limit traces to a resolved Open Question in
docs/design/DESIGN.md."""
from dataclasses import dataclass

MIB = 1024 * 1024  # OQ-2: 1 MB means 1,048,576 bytes


@dataclass(frozen=True)
class Settings:
    data_dir: str = "data"
    max_upload_bytes: int = 1024 * MIB      # OQ-2: 1 GB = 1,073,741,824 bytes, inclusive
    max_pixels: int = 921_600               # OQ-4 / OQ-18: width x height, inclusive
    min_frames: int = 2                     # OQ-3
    min_box_side: int = 8                   # smallest target box / lock zone side, pixels
    area_change_limit: float = 0.5          # Feature 5: more than 50 % between two frames
    tracker: str = "CSRT"
