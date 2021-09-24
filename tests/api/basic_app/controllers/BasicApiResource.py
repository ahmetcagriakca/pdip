from pdi.api.base import ResourceBase
from pdi.api.decorators import controller


@controller()
class BasicApiResource(ResourceBase):
    def get(self, value: int) -> str:
        return "testdata:" + str(value)
