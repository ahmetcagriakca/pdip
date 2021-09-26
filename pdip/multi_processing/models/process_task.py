class ProcessTask:
    def __init__(self,
                 Data: any = None,
                 SubProcessId: int = None,
                 IsFinished: bool = None,
                 IsProcessed: bool = None,
                 State: int = None,
                 Result: any = None,
                 Message: str = None,
                 Exception: Exception = None,
                 Traceback: bool = None):
        self.Data: any = Data
        self.SubProcessId: int = SubProcessId
        self.IsFinished: bool = IsFinished
        self.IsProcessed: bool = IsProcessed
        self.State: int = State
        self.Result: any = Result
        self.Message: str = Message
        self.Exception: Exception = Exception
        self.Traceback: str = Traceback
