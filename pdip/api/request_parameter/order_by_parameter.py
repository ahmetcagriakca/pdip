from dataclasses import dataclass


@dataclass
class OrderByParameter:
    OrderBy: str = None
    Order: str = None
