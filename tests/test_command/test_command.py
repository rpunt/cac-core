"""
Tests for the Command base class functionality.

This module tests the core functionality of the Command class, including argument
parsing, execution flow, error handling, and subclass behavior.
"""

import argparse
import logging
from unittest.mock import patch  # , MagicMock
import pytest

# import cac_core as cac
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
        assert cmd.log.name == "TestCmd"

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

        actions = {action.dest: action for action in parser._actions} # pylint: disable=protected-access
        assert "output" in actions
        assert "test" in actions  # Custom argument

    def test_common_arguments_not_duplicated(self, mock_parser):
        """Test that common arguments aren't added twice."""
        # Add output argument manually
        mock_parser.add_argument("--output", choices=["csv", "json"], default="csv")

        Command.define_common_arguments(mock_parser)

        # Check that there's only one output argument and it hasn't been overridden
        output_actions = [ a for a in mock_parser._actions if a.dest == "output" ]  # pylint: disable=protected-access
        assert len(output_actions) == 1
        assert output_actions[0].choices == [
            "csv",
            "json",
        ]  # Original choices maintained

    def test_abstract_methods(self):
        """Test that abstract methods cannot be instantiated without implementation."""
        with pytest.raises(TypeError):
            Command() # pylint: disable=abstract-class-instantiated

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

    def test_safe_execute_success(self, simple_command):
        """Test that safe_execute handles successful execution."""
        success, result = simple_command.safe_execute({"test": "value"})

        assert success is True
        assert result["status"] == "success"
        assert result["args"]["test"] == "value"

    def test_safe_execute_command_error(self, simple_command):
        """Test that safe_execute handles CommandError."""
        success, result = simple_command.safe_execute({"fail": True})

        assert success is False
        assert isinstance(result, CommandError)
        assert "Command failed" in result.message

    def test_safe_execute_unexpected_error(self, simple_command):
        """Test that safe_execute handles unexpected errors."""
        with patch.object(
            simple_command, "execute", side_effect=ValueError("Unexpected")
        ):
            success, result = simple_command.safe_execute({})

        assert success is False
        assert isinstance(result, CommandError)
        assert "Unexpected error" in result.message

    def test_verbose_mode_changes_log_level(self, simple_command):
        """Test that verbose flag changes log level."""
        original_level = simple_command.log.level

        simple_command.safe_execute({"verbose": True})

        assert simple_command.log.level == logging.DEBUG

        # Reset log level
        simple_command.log.setLevel(original_level)

    def test_validate_args(self, simple_command):
        """Test argument validation."""
        # Base implementation should always return True
        assert simple_command.validate_args({}) is True

        # Test custom validation
        class ValidatingCommand(Command):
            """
            A simple command implementation for testing purposes.
            """

            def define_arguments(self, parser):
                return parser

            def execute(self, args):
                return args

            def validate_args(self, args):
                if "required_arg" not in args:
                    raise CommandError("Missing required argument")
                return True

        cmd = ValidatingCommand()

        # Test direct validation raises error
        with pytest.raises(CommandError) as excinfo:
            cmd.validate_args({})
        assert "Missing required argument" in str(excinfo.value)

        # Test safe_execute properly handles validation errors
        success, result = cmd.safe_execute({})
        assert success is False
        assert isinstance(result, CommandError)
        assert "Missing required argument" in result.message

        # Should pass validation
        success, _ = cmd.safe_execute({"required_arg": "value"})
        assert success is True
