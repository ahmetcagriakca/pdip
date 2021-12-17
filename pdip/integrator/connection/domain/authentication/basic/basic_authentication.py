from dataclasses import dataclass


@dataclass
class BasicAuthentication:
    User: str = None
    Password: str = None
