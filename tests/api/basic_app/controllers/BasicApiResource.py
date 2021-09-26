from pdip.api.base import ResourceBase
from pdip.api.decorators import controller


@controller()
class BasicApiResource(ResourceBase):
    def get(self, value: int) -> str:
        return "testdata:" + str(value)
