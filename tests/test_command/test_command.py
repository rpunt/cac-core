"""
Tests for the Command base class functionality.

This module tests the core functionality of the Command class, including argument
parsing, execution flow, error handling, and subclass behavior.
"""

import argparse
import logging

import pytest

from cac_core.command import Command, CommandError


class TestCommand:
    """Test suite for the Command base class."""

    @pytest.fixture
    def mock_parser(self):
        """Create a mock argument parser."""
        parser = argparse.ArgumentParser()
        return parser

    @pytest.fixture
    def simple_command(self):
        """Create a simple command implementation for testing."""

        class SimpleCommand(Command):
            """
            A simple command implementation for testing purposes.
            """

            def define_arguments(self, parser):
                super().define_common_arguments(parser)
                parser.add_argument("--test", help="Test argument")
                return parser

            def execute(self, args):
                if "fail" in args and args["fail"]:
                    raise CommandError("Command failed")
                return {"status": "success", "args": args}

        return SimpleCommand()

    def test_command_initialization(self):
        """Test that a Command can be properly initialized."""

        class TestCmd(Command):
            """
            A simple command implementation for testing purposes.
            """

            def define_arguments(self, parser):
                return parser

            def execute(self, args):
                return True

        cmd = TestCmd()
        assert cmd.log is not None
        assert isinstance(cmd.log, logging.Logger)
        # The logger is namespaced under the command's module so the runner's
        # package-prefixed --verbose handling reaches it.
        assert cmd.log.name == f"{type(cmd).__module__}.{type(cmd).__name__}"

    def test_initialization_with_log_level(self):
        """A log_level passed to __init__ is applied to the command's logger."""

        class LeveledCmd(Command):
            def define_arguments(self, parser):
                return parser

            def execute(self, args):
                return 0

        cmd = LeveledCmd(log_level=logging.DEBUG)
        assert cmd.log.level == logging.DEBUG

    def test_define_common_arguments(self, mock_parser):
        """Test that common arguments are added to parser."""
        Command.define_common_arguments(mock_parser)

        # # Check that output and verbose arguments were added
        # actions = {action.dest: action for action in mock_parser._actions}

        # assert "output" in actions
        # assert "verbose" in actions
        # assert "help" in actions

        # # Check argument properties
        # assert actions["output"].choices == ["json", "table"]
        # assert actions["output"].default == "table"
        # assert actions["verbose"].action == "store_true"

        # Parse some test arguments
        args = mock_parser.parse_args(["--output", "json"])
        assert args.output == "json"
        assert args.verbose is False

        args = mock_parser.parse_args(["--verbose"])
        assert args.verbose is True

    def test_define_arguments_adds_common_args(self, simple_command, mock_parser):
        """Test that define_arguments adds common arguments."""
        parser = simple_command.define_arguments(mock_parser)

        actions = {action.dest: action for action in parser._actions}  # pylint: disable=protected-access
        assert "output" in actions
        assert "test" in actions  # Custom argument

    def test_common_arguments_not_duplicated(self, mock_parser):
        """Test that common arguments aren't added twice."""
        # Add output argument manually
        mock_parser.add_argument("--output", choices=["csv", "json"], default="csv")

        Command.define_common_arguments(mock_parser)

        # Check that there's only one output argument and it hasn't been overridden
        output_actions = [a for a in mock_parser._actions if a.dest == "output"]  # pylint: disable=protected-access
        assert len(output_actions) == 1
        assert output_actions[0].choices == [
            "csv",
            "json",
        ]  # Original choices maintained

    def test_abstract_methods(self):
        """Test that abstract methods cannot be instantiated without implementation."""
        with pytest.raises(TypeError):
            Command()  # pylint: disable=abstract-class-instantiated

    def test_define_arguments_super_adds_common_args(self):
        """Calling super().define_arguments() adds the common --output/--verbose."""

        class SuperCmd(Command):
            def define_arguments(self, parser):
                super().define_arguments(parser)
                return parser

            def execute(self, args):
                return 0

        parser = argparse.ArgumentParser()
        SuperCmd().define_arguments(parser)
        dests = {a.dest for a in parser._actions}  # pylint: disable=protected-access
        assert "output" in dests
        assert "verbose" in dests

    def test_base_execute_raises_not_implemented(self):
        """The base execute() raises if a subclass delegates to it via super()."""

        class DelegatingCmd(Command):
            def define_arguments(self, parser):
                return parser

            def execute(self, args):
                return super().execute(args)

        with pytest.raises(NotImplementedError):
            DelegatingCmd().execute({})

    def test_execute_implementation(self, simple_command):
        """Test that execute can be called on implementing class."""
        result = simple_command.execute({"test": "value"})
        assert result["status"] == "success"
        assert result["args"]["test"] == "value"

    def test_command_error(self, simple_command):
        """Test that CommandError is properly raised and contains information."""
        with pytest.raises(CommandError) as excinfo:
            simple_command.execute({"fail": True})

        assert "Command failed" in str(excinfo.value)
        assert excinfo.value.exit_code == 1
