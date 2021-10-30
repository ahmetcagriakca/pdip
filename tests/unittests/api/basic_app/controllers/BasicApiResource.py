from pdip.api.base import ResourceBase


class BasicApiResource(ResourceBase):
    def get(self, value: int) -> str:
        return "testdata:" + str(value)
