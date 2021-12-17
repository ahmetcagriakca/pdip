from enum import Enum


class AuthenticationTypes(Enum):
    NoAuthentication = 0
    BasicAuthentication = 1
    Kerberos = 2
