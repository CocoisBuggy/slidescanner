from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class CassetteItem:
    name: str
    label: str
    stars: int
    date: Optional[datetime]


PENDING_CASSETTE = CassetteItem(name="", label="", stars=1, date=None)
