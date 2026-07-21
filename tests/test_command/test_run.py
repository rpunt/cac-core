"""
Tests for the Command.run() template and handle_exception().

Commands implement execute() (the work); the shared CLI runner invokes the base
class's run() wrapper, which maps outcomes and exceptions to exit codes.
"""

from unittest.mock import MagicMock

from cac_core.command import Command


class _Cmd(Command):
    """Concrete command driven via a stubbed execute()."""

    def define_arguments(self, parser):
        parser.add_argument("--name")
        return parser

    def execute(self, args):  # pragma: no cover - replaced per test
        return 0


def _cmd():
    command = _Cmd()
    command.log = MagicMock()
    return command


class TestRun:
    def test_success_return_passed_through(self):
        command = _cmd()
        command.execute = MagicMock(return_value=0)
        assert command.run(object()) == 0

    def test_none_return_treated_as_success(self):
        command = _cmd()
        command.execute = MagicMock(return_value=None)
        assert command.run(object()) == 0

    def test_nonzero_return_passed_through(self):
        command = _cmd()
        command.execute = MagicMock(return_value=2)
        assert command.run(object()) == 2

    def test_exception_mapped_to_nonzero(self):
        command = _cmd()
        command.execute = MagicMock(side_effect=RuntimeError("boom"))
        assert command.run(object()) == 1
        command.log.error.assert_called()

    def test_bool_return_treated_as_failure(self):
        # bool is not a valid exit code; ``return True`` must not become exit 1
        # silently via sys.exit(True). It is a contract violation -> failure+warn.
        command = _cmd()
        command.execute = MagicMock(return_value=True)
        assert command.run(object()) == 1
        command.log.warning.assert_called()

    def test_false_return_treated_as_failure(self):
        command = _cmd()
        command.execute = MagicMock(return_value=False)
        assert command.run(object()) == 1
        command.log.warning.assert_called()

    def test_non_int_return_treated_as_failure(self):
        command = _cmd()
        command.execute = MagicMock(return_value="done")
        assert command.run(object()) == 1
        command.log.warning.assert_called()


class TestHandleException:
    def test_default_logs_and_returns_one(self):
        command = _cmd()
        assert command.handle_exception(ValueError("x")) == 1
        command.log.error.assert_called()


class TestLoggerNamespacing:
    def test_logger_is_package_namespaced(self):
        # The base logger must live under the command's package so the runner's
        # --verbose handling (which raises loggers by package prefix) reaches it.
        command = _Cmd()
        assert command.log.name == f"{_Cmd.__module__}.{_Cmd.__name__}"
        assert command.log.name.startswith(_Cmd.__module__.split(".", 1)[0])
