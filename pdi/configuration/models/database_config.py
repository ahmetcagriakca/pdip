from .base_config import BaseConfig


class DatabaseConfig(BaseConfig):

    def __init__(self,
                 type: str = None,
                 connection_string: str = None,
                 driver: str = None,
                 host: str = None,
                 port: int = None,
                 sid: str = None,
                 service_name: str = None,
                 database: str = None,
                 username: str = None,
                 password: str = None,
                 application_name: str = None
                 ):
        self.connection_string = connection_string
        self.type = type
        self.driver: str = driver
        self.host: str = host
        self.port: int = port
        self.sid: str = sid
        self.service_name: str = service_name
        self.database: str = database
        self.username: str = username
        self.password: str = password
        self.application_name = application_name

    def is_valid(self):
        pass
