from injector import inject

from pdi.api.base import ResourceBase
from pdi.api.decorators import controller
from pdi.logging.loggers.database.sql_logger import SqlLogger


# @inject
# def __init__(self,
#              *args, **kwargs):
#     super().__init__(*args, **kwargs)
@controller()
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
