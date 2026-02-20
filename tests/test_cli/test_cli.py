"""
Test suite for the CLI class in the cac_core module.
"""

from unittest.mock import MagicMock

import pytest

from cac_core.cli import CLI


class TestCLI:
    """Test suite for the CLI class."""

    def test_init_defaults(self):
        """Test CLI initialization with default config."""
        cli = CLI({})
        assert cli.commands == {}
        assert cli.config == {}
        assert cli.opts == {}

    def test_init_with_config(self):
        """Test CLI initialization with custom config."""
        config = {"description": "Test app"}
        cli = CLI({}, config=config)
        assert cli.config == config
        assert cli.parser.description == "Test app"

    def test_parse_args(self):
        """Test argument parsing."""
        cli = CLI({})
        cli.parser.add_argument("--verbose", action="store_true")
        result = cli.parse_args(["--verbose"])
        assert result["verbose"] is True
        assert cli.opts["verbose"] is True

    def test_parse_args_empty(self):
        """Test parsing with no arguments."""
        cli = CLI({})
        result = cli.parse_args([])
        assert isinstance(result, dict)

    def test_execute_no_command(self):
        """Test execute exits when no command is set."""
        cli = CLI({})
        cli.opts = {}
        with pytest.raises(SystemExit) as exc_info:
            cli.execute()
        assert exc_info.value.code == 1

    def test_execute_unknown_command(self):
        """Test execute exits for unknown command."""
        cli = CLI({})
        cli.opts = {"command": "nonexistent"}
        with pytest.raises(SystemExit) as exc_info:
            cli.execute()
        assert exc_info.value.code == 1

    def test_execute_valid_command(self):
        """Test execute calls the correct command module."""
        mock_module = MagicMock()
        cli = CLI({"test": mock_module})
        cli.opts = {"command": "test", "verbose": False}
        cli.execute()
        mock_module.execute.assert_called_once_with(cli.opts)

    def test_execute_command_exception(self):
        """Test execute handles command exceptions gracefully."""
        mock_module = MagicMock()
        mock_module.execute.side_effect = RuntimeError("command failed")
        cli = CLI({"test": mock_module})
        cli.opts = {"command": "test"}
        with pytest.raises(SystemExit) as exc_info:
            cli.execute()
        assert exc_info.value.code == 1
