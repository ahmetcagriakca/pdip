from injector import inject

from pdip.api.base import ResourceBase
from pdip.logging.loggers.sql import SqlLogger


# @inject
# def __init__(self,
#              *args, **kwargs):
#     super().__init__(*args, **kwargs)
class BasicApiWithLogResource(ResourceBase):
    @inject
    def __init__(self,
                 logger: SqlLogger,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger

    def get(self, value: int) -> str:
        self.logger.info('data:' + str(value))
        return "testdata:" + str(value)
