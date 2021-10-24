from injector import inject

from pdip.api.base import ResourceBase
from pdip.api.decorators import controller
from pdip.logging.loggers.database import SqlLogger


# @inject
# def __init__(self,
#              *args, **kwargs):
#     super().__init__(*args, **kwargs)
class BasicApiWithLogResource(ResourceBase):
    @inject
    def __init__(self,
                 sql_logger: SqlLogger,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sql_logger = sql_logger

    def get(self, value: int) -> str:
        self.sql_logger.info('data:' + str(value))
        return "testdata:" + str(value)
