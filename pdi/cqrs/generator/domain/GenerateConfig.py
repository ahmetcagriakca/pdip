from dataclasses import dataclass

from generator.domain.DaoGenerateConfig import DaoGenerateConfig


@dataclass
class GenerateConfig:
    base_directory: str = None
    domain: str = None
    name: str = None
    dao: DaoGenerateConfig = None