import logging
import traceback
from logging import handlers

from injector import inject

from ..base import ILogger
from ....dependency import ISingleton
from ....utils import Utils


class FileLogger(ISingleton, ILogger):
    @inject
    def __init__(self, log_level=logging.DEBUG):
        self.log_level = log_level
        self.logger = logging.getLogger('pdip.file_logger')
        self.file_handler = None
        self.log_init()

    def __del__(self):
        self.logger.removeHandler(self.file_handler)
        del self.file_handler

    def log_init(self):
        """
        initialization of log file.
        """
        if not self.logger.handlers:
            self.logger.setLevel(self.log_level)
            process_info = Utils.get_process_info()
            format = logging.Formatter(
                f"%(asctime)s:%(name)s:%(levelname)s: - {process_info} - %(message)s")

            self.file_handler = handlers.RotatingFileHandler(
                'pdip.log', maxBytes=(1048576 * 5), backupCount=7)
            self.file_handler.setFormatter(format)
            self.logger.addHandler(self.file_handler)

    def log(self, level, message):
        self.logger.log(level, message)

    def exception(self, exception: Exception, message: str = None, job_id=None):
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
