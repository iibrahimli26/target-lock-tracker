"""Boxes in picture pixels, measured from the top-left corner of the frame."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def area(self) -> float:
        return self.w * self.h

    def as_list(self) -> list:
        return [round(self.x, 2), round(self.y, 2), round(self.w, 2), round(self.h, 2)]


def inside(box: Box, zone: Box) -> bool:
    """True when the whole box is inside the zone; touching an edge counts as inside (OQ-23)."""
    return (box.x >= zone.x and box.y >= zone.y
            and box.x + box.w <= zone.x + zone.w
            and box.y + box.h <= zone.y + zone.h)
