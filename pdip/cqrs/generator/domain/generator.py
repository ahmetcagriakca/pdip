from abc import ABC

from .generate_config import GenerateConfig


class Generator(ABC):
    def generate(self, generate_config: GenerateConfig):
        pass
