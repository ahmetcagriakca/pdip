"""Behavioural tests for ``pdip.delivery.email_provider``.

Mocks are placed at the SMTP boundary (``smtplib.SMTP``) and at the
``ConfigService`` / ``SqlLogger`` collaborators. No real SMTP server
is contacted, per ADR-0026 D.2 and the task brief.
"""

import smtplib
from socket import gaierror
from unittest import TestCase
from unittest.mock import MagicMock, patch

from pdip.delivery.email_provider import EmailProvider


def _config_stub(values):
    """Return a ConfigService stub that answers ``get_config_by_name``
    from a dict. Missing keys resolve to ``None``."""
    stub = MagicMock()
    stub.get_config_by_name.side_effect = lambda name: values.get(name)
    return stub


_FULL_CONFIG = {
    "EMAIL_HOST": "smtp.example.com",
    "EMAIL_PORT": 587,
    "EMAIL_SMTP": "sender@example.com",
    "EMAIL_FROM": "from@example.com",
    "EMAIL_USER": "user",
    "EMAIL_PASSWORD": "secret",
}

_NO_AUTH_CONFIG = {
    "EMAIL_HOST": "smtp.example.com",
    "EMAIL_PORT": 25,
    "EMAIL_SMTP": "sender@example.com",
    "EMAIL_FROM": "from@example.com",
    "EMAIL_USER": "",
    "EMAIL_PASSWORD": "",
}


class SendAbortsWhenConfigurationIncomplete(TestCase):
    def test_send_logs_error_and_skips_smtp_when_host_missing(self):
        # Arrange
        logger = MagicMock()
        config = _config_stub({})  # every key resolves to None
        provider = EmailProvider(config_service=config, logger=logger)

        with patch("pdip.delivery.email_provider.smtplib.SMTP") as smtp_cls:
            # Act
            provider.send(["to@example.com"], "Subject", "<p>body</p>")

        # Assert
        smtp_cls.assert_not_called()
        logger.error.assert_called_once_with("Email not configured")
        logger.info.assert_not_called()

    def test_send_logs_error_when_smtp_address_missing(self):
        # Arrange
        logger = MagicMock()
        config = _config_stub({"EMAIL_HOST": "smtp.example.com"})
        provider = EmailProvider(config_service=config, logger=logger)

        with patch("pdip.delivery.email_provider.smtplib.SMTP") as smtp_cls:
            # Act
            provider.send(["to@example.com"], "Subject", "body")

        # Assert
        smtp_cls.assert_not_called()
        logger.error.assert_called_once_with("Email smtp not configured")

    def test_send_logs_error_when_from_address_missing(self):
        # Arrange
        logger = MagicMock()
        config = _config_stub(
            {
                "EMAIL_HOST": "smtp.example.com",
                "EMAIL_SMTP": "sender@example.com",
            }
        )
        provider = EmailProvider(config_service=config, logger=logger)

        with patch("pdip.delivery.email_provider.smtplib.SMTP") as smtp_cls:
            # Act
            provider.send(["to@example.com"], "Subject", "body")

        # Assert
        smtp_cls.assert_not_called()
        logger.error.assert_called_once_with(
            "Email from_address not configured"
        )


class SendDispatchesThroughSmtpWhenConfigComplete(TestCase):
    def test_send_logs_into_smtp_with_tls_when_credentials_present(self):
        # Arrange
        logger = MagicMock()
        config = _config_stub(_FULL_CONFIG)
        provider = EmailProvider(config_service=config, logger=logger)
        smtp_instance = MagicMock()

        with patch(
            "pdip.delivery.email_provider.smtplib.SMTP",
            return_value=smtp_instance,
        ) as smtp_cls:
            # Act
            provider.send(["a@example.com", "b@example.com"], "Subj", "<p>B</p>")

        # Assert
        smtp_cls.assert_called_once_with("smtp.example.com", 587)
        smtp_instance.ehlo.assert_called_once()
        smtp_instance.starttls.assert_called_once()
        smtp_instance.login.assert_called_once_with("user", "secret")
        smtp_instance.sendmail.assert_called_once()
        args, _ = smtp_instance.sendmail.call_args
        self.assertEqual(args[0], "sender@example.com")
        self.assertEqual(args[1], ["a@example.com", "b@example.com"])
        # The MIME payload is the third argument; confirm recipients and subject.
        payload = args[2]
        self.assertIn("Subject: Subj", payload)
        self.assertIn("a@example.com, b@example.com", payload)
        smtp_instance.quit.assert_called_once()
        smtp_instance.close.assert_called_once()
        logger.info.assert_called_once_with("Email sent successfully")
        logger.error.assert_not_called()

    def test_send_skips_login_when_credentials_are_empty(self):
        # Arrange
        logger = MagicMock()
        config = _config_stub(_NO_AUTH_CONFIG)
        provider = EmailProvider(config_service=config, logger=logger)
        smtp_instance = MagicMock()

        with patch(
            "pdip.delivery.email_provider.smtplib.SMTP",
            return_value=smtp_instance,
        ):
            # Act
            provider.send(["a@example.com"], "Hello", "body")

        # Assert
        smtp_instance.login.assert_not_called()
        smtp_instance.starttls.assert_not_called()
        smtp_instance.ehlo.assert_not_called()
        smtp_instance.sendmail.assert_called_once()
        logger.info.assert_called_once_with("Email sent successfully")


class SendHandlesNetworkAndSmtpErrorsGracefully(TestCase):
    def test_gaierror_is_caught_and_logged(self):
        # Arrange
        logger = MagicMock()
        config = _config_stub(_FULL_CONFIG)
        provider = EmailProvider(config_service=config, logger=logger)

        with patch(
            "pdip.delivery.email_provider.smtplib.SMTP",
            side_effect=gaierror("dns fail"),
        ):
            # Act
            provider.send(["a@example.com"], "s", "b")

        # Assert
        self.assertTrue(logger.error.called)
        error_msg = logger.error.call_args[0][0]
        self.assertIn("Failed to connect to the server", error_msg)
        self.assertIn("dns fail", error_msg)
        logger.info.assert_not_called()

    def test_connection_refused_is_caught_and_logged(self):
        # Arrange
        logger = MagicMock()
        config = _config_stub(_FULL_CONFIG)
        provider = EmailProvider(config_service=config, logger=logger)

        with patch(
            "pdip.delivery.email_provider.smtplib.SMTP",
            side_effect=ConnectionRefusedError("refused"),
        ):
            # Act
            provider.send(["a@example.com"], "s", "b")

        # Assert
        logger.error.assert_called_once()
        self.assertIn(
            "refused", logger.error.call_args[0][0]
        )
        logger.info.assert_not_called()

    def test_smtp_server_disconnected_is_caught_and_logged(self):
        # Arrange
        logger = MagicMock()
        config = _config_stub(_FULL_CONFIG)
        provider = EmailProvider(config_service=config, logger=logger)

        with patch(
            "pdip.delivery.email_provider.smtplib.SMTP",
            side_effect=smtplib.SMTPServerDisconnected("gone"),
        ):
            # Act
            provider.send(["a@example.com"], "s", "b")

        # Assert
        logger.error.assert_called_once()
        self.assertIn(
            "Wrong user/password", logger.error.call_args[0][0]
        )
        logger.info.assert_not_called()

    def test_generic_smtp_exception_is_caught_and_logged(self):
        # Arrange
        logger = MagicMock()
        config = _config_stub(_FULL_CONFIG)
        provider = EmailProvider(config_service=config, logger=logger)
        smtp_instance = MagicMock()
        smtp_instance.sendmail.side_effect = smtplib.SMTPException("boom")

        with patch(
            "pdip.delivery.email_provider.smtplib.SMTP",
            return_value=smtp_instance,
        ):
            # Act
            provider.send(["a@example.com"], "s", "b")

        # Assert
        logger.error.assert_called_once()
        self.assertIn("SMTP error occurred", logger.error.call_args[0][0])
        # quit() in the inner finally still fires before the except block.
        smtp_instance.quit.assert_called_once()
        # Outer finally closes the handle too.
        smtp_instance.close.assert_called_once()
        logger.info.assert_not_called()
