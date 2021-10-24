from dataclasses import dataclass

from ..base.base_config import BaseConfig


@dataclass
class ApiConfig(BaseConfig):
    base_url: str = None
    doc_url: str = None
    is_debug: bool = None
    version: str = None
    port: int = None
    origins: str = None
    authorizations: any = None
    security: any = None
