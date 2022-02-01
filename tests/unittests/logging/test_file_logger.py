from unittest import TestCase

from pdip.logging.loggers.file import FileLogger


class TestProcessManager(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        return super().tearDown()

    @classmethod
    def process_method(cls, sub_process_id, data):
        print(f"{sub_process_id}-{data}")
        return data

    def test_log(self):
        file_logger = FileLogger()
        file_logger.debug('debug')
        file_logger.info('info')
        file_logger.warning('warning')
        file_logger.error('error')
        file_logger.fatal('fatal')
        del file_logger