from pdi.api.base import ResourceBase
from pdi.api.decorators import controller
from pdi.exceptions import OperationalException


@controller()
class BasicApiWithErrorResource(ResourceBase):
    def get(self, value: int) -> str:
        raise OperationalException(f"Value:{value} getting error")
        return "testdata:" + str(value)
