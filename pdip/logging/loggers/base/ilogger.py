from abc import abstractmethod
from datetime import datetime

from ....utils import Utils


class ILogger:

    def log_init(self):
        """
        initialization of log file.
        """
        pass

    def prepare_message(message):
        log_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        process_info = Utils.get_process_info()
        return f'{log_datetime} - {process_info} - {message} '

    @abstractmethod
    def log(self, level, message):
        pass

    @abstractmethod
    def exception(self, exception: Exception, message: str = None):
        pass

    def critical(self, message):
        pass

    @abstractmethod
    def fatal(self, message):
        pass

    @abstractmethod
    def error(self, message):
        pass

    @abstractmethod
    def warning(self, message):
        pass

    @abstractmethod
    def info(self, message):
        pass

    @abstractmethod
    def debug(self, message):
        pass
