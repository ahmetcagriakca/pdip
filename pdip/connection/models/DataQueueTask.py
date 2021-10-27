from dataclasses import dataclass


@dataclass
class DataQueueTask:
    Id: int = None
    Data: any = None
    DataTypes: any = None
    IsDataFrame: bool = True
    Start: int = None
    End: int = None
    Limit: int = None
    State: int = None
    IsFinished: bool = None
    IsProcessed: bool = None
    Message: str = None
    Traceback: str = None
    Exception: Exception = None
