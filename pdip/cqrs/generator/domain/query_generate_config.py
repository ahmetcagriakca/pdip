from dataclasses import dataclass

from .generate_config import GenerateConfig


@dataclass
class QueryGenerateConfig(GenerateConfig):
    is_list: bool = True
    has_paging: bool = False
