class BaseLogger:
    def __init__(self):
        pass

    #######################################################################################
    def logger_method(self, level, message, job_id=None):
        self.log_to_db(level=level, message=message, job_id=job_id)

    def log(self, level, message):
        prepared_message = self.prepare_message(message)
        self.logger.log(level, prepared_message)

    def fatal(self, message):
        prepared_message = self.prepare_message(message)
        self.logger.fatal(prepared_message)

    def error(self, message):
        prepared_message = self.prepare_message(message)
        self.logger.error(prepared_message)

    def warning(self, message):
        prepared_message = self.prepare_message(message)
        self.logger.warning(prepared_message)

    def info(self, message):
        prepared_message = self.prepare_message(message)
        self.logger.info(prepared_message)

    def debug(self, message):
        prepared_message = self.prepare_message(message)
        self.logger.debug(prepared_message)
