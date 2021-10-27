from dataclasses import dataclass


@dataclass
class PagingParameter:
    PageNumber: int = None
    PageSize: int = None
