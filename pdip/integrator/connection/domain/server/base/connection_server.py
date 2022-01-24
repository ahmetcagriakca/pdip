from dataclasses import dataclass


@dataclass
class ConnectionServer:
    Host: str = None
    Port: int = None
