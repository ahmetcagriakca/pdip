from dataclasses import dataclass


@dataclass
class Server:
    Host: str = None
    Port: int = None
