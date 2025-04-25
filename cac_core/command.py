"""
Command module for the CAC Core package.

This module provides the Command class which serves as the base class for all
command implementations in the CAC framework. It defines the structure and
common functionality that all commands should implement.
"""

import abc
import logging
from typing import Any, Dict, Optional, Tuple, Union #, List


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
        self.log = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def define_common_arguments(parser) -> None:
        """
        Defines common arguments for all command parsers.

        Args:
            parser (ArgumentParser): The argument parser to add arguments to
        """
        has_output = any(action.dest == 'output' for action in parser._actions)
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
        has_verbose = any(action.dest == 'verbose' for action in parser._actions)
        if not has_verbose:
            parser.add_argument(
                "--verbose",
                help="Verbose output",
                action="store_true",
                default=False
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

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """
        Validate command arguments before execution.

        Args:
            args (dict): Dictionary of parsed command-line arguments

        Raises:
            CommandError: If arguments are invalid

        Returns:
            bool: True if arguments are valid
        """
        # Base implementation does nothing, subclasses can override
        return True

    def safe_execute(
        self, args: Dict[str, Any]
    ) -> Tuple[bool, Union[Any, CommandError]]:
        """
        Safely execute the command with exception handling.

        Args:
            args (dict): Dictionary of parsed command-line arguments

        Returns:
            tuple: (success, result_or_error)
        """
        try:
            # Set log level if verbose flag is present
            if args.get("verbose", False):
                self.log.setLevel(logging.DEBUG)

            # Validate arguments first
            self.validate_args(args)

            # Execute the command
            result = self.execute(args)
            return True, result

        except CommandError as e:
            self.log.error(e.message)
            return False, e

        except Exception as e:
            # Catch unexpected exceptions
            self.log.exception(f"Unexpected error executing {self.__class__.__name__}")
            return False, CommandError(f"Unexpected error: {str(e)}")
