from abc import ABC

from generator.domain.GenerateConfig import GenerateConfig


class Generator(ABC):
    def generate(self, generate_config: GenerateConfig):
        pass