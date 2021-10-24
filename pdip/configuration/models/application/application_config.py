from dataclasses import dataclass

from ..base.base_config import BaseConfig


@dataclass
class ApplicationConfig(BaseConfig):
    root_directory: str = None
    name: str = None
    environment: str = None
    hostname: str = None
    secret_key: str = None
