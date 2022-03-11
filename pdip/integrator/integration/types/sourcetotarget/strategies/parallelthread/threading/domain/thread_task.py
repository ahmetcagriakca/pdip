from dataclasses import dataclass


@dataclass
class ThreadTask:
    Id: int = None
    Data: any = None
    IsFinished: bool = None
    IsProcessed: bool = None
    State: int = None
    Result: any = None
    Message: str = None
    Exception: Exception = None
    Traceback: bool = None
