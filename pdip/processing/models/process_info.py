import multiprocessing


class ProcessInfo:
    def __init__(self,
                 Process: any = None,
                 SubProcessId: int = None,
                 IsFinished: bool = False):
        self.Process: multiprocessing.Process = Process
        self.SubProcessId: int = SubProcessId
        self.IsFinished: bool = IsFinished
