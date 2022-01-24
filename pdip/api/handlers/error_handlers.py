import json
import traceback

from injector import inject

from ...data.repository import RepositoryProvider
from ...dependency import ISingleton
from ...dependency.provider import ServiceProvider
from ...logging.loggers.sql import SqlLogger


class ErrorHandlers(ISingleton):
    @inject
    def __init__(
            self,
            logger: SqlLogger,
            service_provider: ServiceProvider
    ):
        self.service_provider = service_provider
        self.logger = logger
        self.separator = '|'
        self.default_content_type = "application/json"
        self.mime_type_string = "mimetype"

    def handle_http_exception(self, exception):
        """Return JSON instead of HTML for HTTP errors."""
        # start with the correct headers and status code from the error
        response = exception.get_response()
        # replace the body with JSON
        response.data = json.dumps({
            "Result": "",
            "IsSuccess": "false",
            "Code": exception.code,
            "Name": exception.name,
            "Message": exception.description,
        })
        message = "empty"
        if exception is not None and exception.description is not None:
            message = exception.description
        self.logger.error(f'code:{exception.code} - name:{exception.name} - Message:{message}')
        response.content_type = self.default_content_type
        return response

    def handle_exception(self, exception):
        """Return JSON instead of HTML for HTTP errors."""
        self.service_provider.get(RepositoryProvider).rollback()
        # start with the correct headers and status code from the error
        exception_traceback = traceback.format_exc()
        output = self.separator.join(exception.args)
        # replace the body with JSON
        # response = json.dumps({
        #     "result": "",
        #     "isSuccess": "false",
        #     "message": f"ConnectionServer exception occurred. Exception Message:{output}",
        # })
        output_message = "empty"
        if output is not None and output != "":
            output_message = output
        trace_message = "empty"
        if exception_traceback is not None and exception_traceback != "":
            trace_message = exception_traceback
        self.logger.error(f'Messsage:{output_message} - Trace:{trace_message}')
        return {
                   "Result": "",
                   "IsSuccess": "false",
                   "Message": f"ConnectionServer exception occurred. Exception Message:{output}",
               }, 500, {self.mime_type_string: self.default_content_type}

    def handle_operational_exception(self, exception):
        separator = '|'
        default_content_type = "application/json"
        mime_type_string = "mimetype"
        """Return JSON instead of HTML for HTTP errors."""
        self.service_provider.get(RepositoryProvider).rollback()
        # start with the correct headers and status code from the error
        exception_traceback = traceback.format_exc()
        output = separator.join(exception.args)
        output_message = "empty"
        if output is not None and output != "":
            output_message = output
        trace_message = "empty"
        if exception_traceback is not None and exception_traceback != "":
            trace_message = exception_traceback
        self.logger.error(
            f'Operational Exception Messsage:{output_message} - Trace:{trace_message}')
        return {
                   "Result": "",
                   "IsSuccess": "false",
                   "Message": output
               }, 400, {mime_type_string: default_content_type}
