from dataclasses import dataclass


@dataclass
class TaskMessage:
    event: any = None
    is_finished: bool = None
    args: () = None
    kwargs: {} = None
