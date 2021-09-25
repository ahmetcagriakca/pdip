from .base_config import BaseConfig


class ApiConfig(BaseConfig):

    def __init__(self,
                 is_debug: bool = None,
                 port: int = None,
                 origins: str = None,
                 authorizations: any = None,
                 security: any = None):
        self.port: int = port
        self.is_debug: bool = is_debug
        self.origins: str = origins
        self.authorizations: any = authorizations
        self.security: any = security
