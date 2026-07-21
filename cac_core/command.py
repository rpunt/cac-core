"""
Command module for the CAC Core package.

This module provides the Command class which serves as the base class for all
command implementations in the CAC framework. It defines the structure and
common functionality that all commands should implement.
"""

import abc
import logging
from typing import Any, Dict, Optional


class CommandError(Exception):
    """Exception raised for command execution errors."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(self.message)


class Command(metaclass=abc.ABCMeta):
    """
    Abstract base class for all commands in the CAC framework.

    This class defines the interface that all command implementations must follow,
    with abstract methods for setting up parsers and executing commands. It also
    provides utility methods for output formatting.

    Attributes:
        log (Logger): Logger instance for the command
    """

    def __init__(self, log_level: Optional[int] = None):
        """
        Initialize the command.
        """
        # Namespace the logger under the command's package (e.g.
        # ``cac_jira.commands.issue.show.IssueShow``) rather than the bare class
        # name. The shared runner's ``--verbose`` handling raises every logger
        # whose name starts with the tool package, so a bare ``IssueShow`` logger
        # would be silently missed.
        self.log = logging.getLogger(f"{type(self).__module__}.{type(self).__name__}")
        if log_level is not None:
            self.log.setLevel(log_level)

    @staticmethod
    def define_common_arguments(parser) -> None:
        """
        Defines common arguments for all command parsers.

        Args:
            parser (ArgumentParser): The argument parser to add arguments to
        """
        has_output = any(action.dest == "output" for action in parser._actions)
        if not has_output:
            parser.add_argument(
                "--output",
                help="Output format",
                choices=["json", "table"],
                default="table",
                type=str,
                metavar="FORMAT",
            )

        # Check if the verbose argument already exists
        has_verbose = any(action.dest == "verbose" for action in parser._actions)
        if not has_verbose:
            parser.add_argument(
                "--verbose", help="Verbose output", action="store_true", default=False
            )

    @abc.abstractmethod
    def define_arguments(self, parser) -> Any:
        """
        Define command-specific arguments.

        This method must be implemented by subclasses to add
        command-specific arguments to the parser.

        Args:
            parser: The argument parser to add arguments to

        Returns:
            The updated argument parser
        """
        # Add common arguments first
        self.define_common_arguments(parser)
        return parser

    @abc.abstractmethod
    def execute(self, args: Dict[str, Any]) -> Any:
        """
        Execute the command with the given arguments.

        This abstract method must be implemented by all command subclasses.

        Args:
            args (dict): Dictionary of parsed command-line arguments
        """
        raise NotImplementedError("Command subclasses must implement execute()")

    def run(self, args: Any) -> int:
        """
        Run the command and map its outcome to a process exit code.

        This is the template method the shared CLI runner invokes. It calls the
        subclass's ``execute()`` and turns any raised exception into a logged,
        non-zero exit code via ``handle_exception``. Centralizing this here means
        individual commands implement ``execute()`` as straight-line logic and
        may raise freely (or return a non-zero int for their own validation
        failures) without each writing their own try/except.

        ``execute()`` must return an ``int`` exit code or ``None`` (treated as
        ``0``). Any other return -- including a ``bool`` -- is a contract
        violation: it is logged and treated as failure, so a stray ``return
        True``/``return "..."`` can never be handed to ``sys.exit`` and silently
        invert or corrupt the process exit code.

        Args:
            args: The parsed arguments.

        Returns:
            int: ``0`` on success, non-zero on failure.
        """
        try:
            result = self.execute(args)
        except Exception as e:  # pylint: disable=broad-exception-caught
            return self.handle_exception(e)
        if result is None:
            return 0
        # bool is an int subclass, so guard it explicitly -- otherwise
        # ``return True`` would become exit code 1 and ``return False`` exit 0.
        if isinstance(result, bool) or not isinstance(result, int):
            self.log.warning(
                "%s.execute() returned %r; expected an int exit code or None. "
                "Treating it as failure.",
                type(self).__name__,
                result,
            )
            return 1
        return result

    def handle_exception(self, exc: Exception) -> int:
        """
        Map an exception raised by ``execute()`` to an exit code.

        The default logs the error (with a traceback when debug logging is on,
        e.g. ``--verbose``) and returns ``1``. Subclasses override this to give
        friendlier messages for domain-specific exceptions, typically calling
        ``super().handle_exception(exc)`` for anything they don't recognize.

        Args:
            exc: The exception raised by ``execute()``.

        Returns:
            int: A non-zero exit code.
        """
        self.log.error(
            "%s failed: %s",
            type(self).__name__,
            exc,
            exc_info=self.log.isEnabledFor(logging.DEBUG),
        )
        return 1
