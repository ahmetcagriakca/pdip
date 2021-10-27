from dataclasses import dataclass

from .dao_generate_config import DaoGenerateConfig


@dataclass
class GenerateConfig:
    base_directory: str = None
    domain: str = None
    name: str = None
    dao: DaoGenerateConfig = None
