"""Unit tests for ``pdip.data.seed.seed_runner.SeedRunner``.

``SeedRunner.run`` connects the database, iterates ``Seed.__subclasses__()``,
instantiates each seed via the DI provider, and calls ``.seed()``. The
failure paths — DI lookup fails (fall back to default ctor), database
connect raises ``OperationalError``, unexpected exception — are all
logged and non-fatal. Tests cover each branch.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import OperationalError

from pdip.data.base import DatabaseSessionManager
from pdip.data.seed.seed import Seed
from pdip.data.seed.seed_runner import SeedRunner


def _build_runner():
    logger = MagicMock(name="SqlLogger")
    service_provider = MagicMock(name="ServiceProvider")
    runner = SeedRunner(logger=logger, service_provider=service_provider)
    return runner, logger, service_provider


class _RecordingSeed(Seed):
    def seed(self):  # pragma: no cover - replaced in tests via MagicMock
        self.ran = True


class SeedRunnerIteratesSubclasses(TestCase):
    def test_run_connects_session_manager_and_runs_seed_instance(self):
        runner, logger, service_provider = _build_runner()
        session_manager = MagicMock(spec=DatabaseSessionManager)
        seed_instance = MagicMock()
        seed_class = MagicMock()

        def resolve(requested):
            if requested is DatabaseSessionManager:
                return session_manager
            if requested is seed_class:
                return seed_instance
            return MagicMock()

        service_provider.get.side_effect = resolve

        with patch.object(Seed, "__subclasses__", return_value=[seed_class]):
            runner.run()

        session_manager.connect.assert_called_once()
        seed_instance.seed.assert_called_once()
        # ``finally`` closes the session manager.
        session_manager.close.assert_called_once()
        logger.exception.assert_not_called()

    def test_run_falls_back_to_default_ctor_when_di_lookup_fails(self):
        runner, logger, service_provider = _build_runner()
        session_manager = MagicMock(spec=DatabaseSessionManager)
        seed_class = MagicMock()
        fallback_instance = MagicMock()
        seed_class.return_value = fallback_instance

        def resolve(requested):
            if requested is DatabaseSessionManager:
                return session_manager
            if requested is seed_class:
                raise KeyError("not registered")
            return MagicMock()

        service_provider.get.side_effect = resolve

        with patch.object(Seed, "__subclasses__", return_value=[seed_class]):
            runner.run()

        seed_class.assert_called_once_with()
        fallback_instance.seed.assert_called_once()
        # The DI lookup failure is logged via logger.exception.
        logger.exception.assert_called_once()

    def test_run_continues_to_next_subclass_when_fallback_ctor_raises(self):
        # Regression: the fallback ``seed_class()`` + ``.seed()`` call
        # previously ran outside the per-subclass try/except, so a
        # broken fallback propagated out of the loop and skipped every
        # remaining subclass. After the fix, the fallback failure is
        # logged and the loop moves on.
        runner, logger, service_provider = _build_runner()
        session_manager = MagicMock(spec=DatabaseSessionManager)

        broken_class = MagicMock(name="broken_seed_class")
        broken_class.side_effect = RuntimeError("ctor exploded")

        good_class = MagicMock(name="good_seed_class")
        good_instance = MagicMock()
        good_class.return_value = good_instance  # not reached on happy path

        def resolve(requested):
            if requested is DatabaseSessionManager:
                return session_manager
            if requested is good_class:
                return good_instance
            # Force a DI failure for the broken class so the fallback runs.
            raise KeyError("not registered")

        service_provider.get.side_effect = resolve

        with patch.object(
            Seed, "__subclasses__", return_value=[broken_class, good_class]
        ):
            runner.run()

        # The broken fallback logged an exception, and the good class
        # still got its .seed() call — the loop did not abort.
        good_instance.seed.assert_called_once()
        # Two exceptions logged for the broken class (DI failure +
        # fallback ctor failure); none for the good class.
        self.assertGreaterEqual(logger.exception.call_count, 2)

    def test_run_logs_operational_error_when_connect_fails(self):
        runner, logger, service_provider = _build_runner()
        session_manager = MagicMock(spec=DatabaseSessionManager)
        op_error = OperationalError("stmt", {}, Exception("boom"))
        session_manager.connect.side_effect = op_error
        service_provider.get.return_value = session_manager

        runner.run()

        logger.exception.assert_called_once()
        args = logger.exception.call_args.args
        self.assertIs(args[0], op_error)
        self.assertIn("Database connection", args[1])
        # ``finally`` still closes the session manager.
        session_manager.close.assert_called_once()

    def test_run_logs_generic_exception_from_subclass_resolution(self):
        runner, logger, service_provider = _build_runner()
        session_manager = MagicMock(spec=DatabaseSessionManager)
        unexpected = RuntimeError("kaboom")

        # The DI call for the DatabaseSessionManager succeeds; the
        # subclass iteration is the place where a generic error lands.
        def resolve(requested):
            if requested is DatabaseSessionManager:
                return session_manager
            raise MagicMock()

        service_provider.get.side_effect = resolve

        def failing_subclasses():
            raise unexpected

        with patch.object(Seed, "__subclasses__", side_effect=failing_subclasses):
            runner.run()

        logger.exception.assert_called_once()
        args = logger.exception.call_args.args
        self.assertIs(args[0], unexpected)
        self.assertIn("Seeds getting error", args[1])

    def test_run_closes_session_manager_in_finally_even_on_error(self):
        runner, _, service_provider = _build_runner()
        session_manager = MagicMock(spec=DatabaseSessionManager)
        session_manager.connect.side_effect = RuntimeError("connect failed")
        service_provider.get.return_value = session_manager

        runner.run()

        # ``finally`` branch still calls close() on the manager it looked
        # up a second time via service_provider.
        session_manager.close.assert_called_once()
