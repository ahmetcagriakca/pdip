from typing import Generic, TypeVar

CQ = TypeVar('CQ', covariant=True)


class CommandQueryBase(Generic[CQ]):
    def __init__(self) -> CQ:
        pass
