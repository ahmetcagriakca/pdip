from dataclasses import dataclass


@dataclass
class ConnectionBasicAuthentication:
    User: str = None
    Password: str = None
