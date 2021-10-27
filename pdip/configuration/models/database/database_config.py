from dataclasses import dataclass

from ..base.base_config import BaseConfig


@dataclass
class DatabaseConfig(BaseConfig):
    type: str = None
    connection_string: str = None
    driver: str = None
    host: str = None
    port: int = None
    sid: str = None
    service_name: str = None
    database: str = None
    user: str = None
    password: str = None
    application_name: str = None
    execution_options: str = None
