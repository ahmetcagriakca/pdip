from pdip.api.base import ResourceBase
from pdip.api.decorators import controller
from pdip.exceptions import OperationalException


@controller()
class BasicApiWithErrorResource(ResourceBase):
    def get(self, value: int) -> str:
        raise OperationalException(f"Value:{value} getting error")
        return "testdata:" + str(value)
