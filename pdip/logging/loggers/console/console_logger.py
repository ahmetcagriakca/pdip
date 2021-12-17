import logging
import sys
import traceback

from injector import inject

from ..base import ILogger
from ....dependency import ISingleton
from ....utils import Utils


class ConsoleLogger(ISingleton, ILogger):
    @inject
    def __init__(self, log_level=logging.DEBUG):
        self.log_level = log_level
        self.logger = logging.getLogger('pdip.console_logger')
        self.console_handler = None
        self.log_init()

    def __del__(self):
        self.logger.removeHandler(self.console_handler)
        del self.console_handler

    def log_init(self):
        """
        initialization of log file.
        """
        if not self.logger.handlers:
            self.logger.setLevel(self.log_level)
            process_info = Utils.get_process_info()
            format = logging.Formatter(f"%(asctime)s:%(name)s:%(levelname)s: - {process_info} - %(message)s")
            self.console_handler = logging.StreamHandler(sys.stdout)
            self.console_handler.setFormatter(format)
            self.logger.addHandler(self.console_handler)

    def log(self, level, message):
        self.logger.log(level, message)

    def exception(self, exception: Exception, message: str = None):
        exc = traceback.format_exc() + '\n' + str(exception)
        if message is not None:
            message += f"Error: {exc}"
        else:
            message = f"Error: {exc}"
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def fatal(self, message):
        self.logger.fatal(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)
