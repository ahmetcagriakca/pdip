from enum import Enum


class ConnectionTypes(Enum):
    Sql = 1
    File = 2
    Queue = 3
    BigData = 4
    WebService = 5
