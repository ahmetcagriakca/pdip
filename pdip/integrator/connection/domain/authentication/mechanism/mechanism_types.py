from enum import Enum


class MechanismTypes(Enum):
    NoAuthentication = 0
    Kerberos = 1
    UserName = 2
    UserNamePassword = 3
