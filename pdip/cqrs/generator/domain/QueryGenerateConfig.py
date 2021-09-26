from dataclasses import dataclass

from generator.domain.GenerateConfig import GenerateConfig


@dataclass
class QueryGenerateConfig(GenerateConfig):
    is_list: bool = True
    has_paging: bool = False
