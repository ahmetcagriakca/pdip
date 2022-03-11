from dataclasses import dataclass


@dataclass
class ThreadInfo:
    Id: int = None
    Thread: any = None
    IsFinished: bool = False
