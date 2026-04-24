"""Unit tests for ``pdip.api.handlers.error_handlers.ErrorHandlers``.

The handler translates exceptions into JSON payloads, logs them, and
rolls back the repository. These tests mock the logger and service
provider (true collaborators) and assert on the JSON body, the status
code, and the rollback/log side effects.
"""

import json
from unittest import TestCase
from unittest.mock import MagicMock

from pdip.api.handlers.error_handlers import ErrorHandlers


def _build_handler():
    logger = MagicMock(name="SqlLogger")
    service_provider = MagicMock(name="ServiceProvider")
    repository_provider = MagicMock(name="RepositoryProvider")
    service_provider.get.return_value = repository_provider
    handler = ErrorHandlers(logger=logger, service_provider=service_provider)
    return handler, logger, service_provider, repository_provider


class ErrorHandlersTranslatesHttpExceptions(TestCase):
    def test_http_exception_response_contains_code_name_and_message(self):
        handler, logger, _, _ = _build_handler()
        response = MagicMock()
        exception = MagicMock()
        exception.get_response.return_value = response
        exception.code = 404
        exception.name = "Not Found"
        exception.description = "resource missing"

        result = handler.handle_http_exception(exception)

        body = json.loads(response.data)
        self.assertEqual(body["Code"], 404)
        self.assertEqual(body["Name"], "Not Found")
        self.assertEqual(body["Message"], "resource missing")
        self.assertEqual(body["IsSuccess"], "false")
        self.assertIs(result, response)

    def test_http_exception_response_sets_json_content_type(self):
        handler, _, _, _ = _build_handler()
        response = MagicMock()
        exception = MagicMock()
        exception.get_response.return_value = response
        exception.code = 500
        exception.name = "Internal"
        exception.description = "boom"

        handler.handle_http_exception(exception)

        self.assertEqual(response.content_type, "application/json")

    def test_http_exception_logs_error_with_formatted_fields(self):
        handler, logger, _, _ = _build_handler()
        exception = MagicMock()
        exception.get_response.return_value = MagicMock()
        exception.code = 418
        exception.name = "Teapot"
        exception.description = "short and stout"

        handler.handle_http_exception(exception)

        logger.error.assert_called_once()
        message = logger.error.call_args.args[0]
        self.assertIn("418", message)
        self.assertIn("Teapot", message)
        self.assertIn("short and stout", message)


class ErrorHandlersTranslatesApplicationExceptions(TestCase):
    def test_generic_exception_returns_500_payload_and_rolls_back(self):
        handler, logger, service_provider, repository_provider = _build_handler()
        exception = Exception("first", "second")

        body, status_code, headers = handler.handle_exception(exception)

        self.assertEqual(status_code, 500)
        self.assertEqual(body["IsSuccess"], "false")
        self.assertIn("first|second", body["Message"])
        self.assertEqual(headers, {"mimetype": "application/json"})
        repository_provider.rollback.assert_called_once()
        logger.error.assert_called_once()

    def test_generic_exception_with_empty_args_logs_empty_placeholder(self):
        handler, logger, _, _ = _build_handler()
        exception = Exception()

        body, _, _ = handler.handle_exception(exception)

        self.assertEqual(body["Message"], "ConnectionServer exception occurred. Exception Message:")
        log_message = logger.error.call_args.args[0]
        self.assertIn("Messsage:empty", log_message)

    def test_operational_exception_returns_400_with_concatenated_args(self):
        handler, logger, _, repository_provider = _build_handler()
        exception = Exception("bad", "input")

        body, status_code, headers = handler.handle_operational_exception(exception)

        self.assertEqual(status_code, 400)
        self.assertEqual(body["Message"], "bad|input")
        self.assertEqual(body["IsSuccess"], "false")
        self.assertEqual(headers, {"mimetype": "application/json"})
        repository_provider.rollback.assert_called_once()
        logger.error.assert_called_once()

    def test_operational_exception_empty_args_uses_empty_placeholder_in_log(self):
        handler, logger, _, _ = _build_handler()
        exception = Exception()

        handler.handle_operational_exception(exception)

        log_message = logger.error.call_args.args[0]
        self.assertIn("Operational Exception Messsage:empty", log_message)
