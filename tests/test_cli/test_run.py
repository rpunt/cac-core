"""
Tests for the shared CLI runner (``cac_core.cli.run``) and its discovery.

The runner scans a package's ``commands/`` tree, builds a nested argparse
parser, wires up argcomplete, and dispatches to the selected action's
``run(args)`` method. These tests exercise that against a throwaway package
built on disk so discovery works exactly as it does for a real ``cac-*`` CLI.
"""

import builtins
import importlib
import os
import sys
import textwrap

import pytest

from cac_core import cli


@pytest.fixture
def fake_pkg(tmp_path, monkeypatch):
    """Create an importable throwaway CLI package and yield its name."""
    pkg = tmp_path / "fakecli"
    (pkg / "commands" / "greet").mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "commands" / "__init__.py").write_text("")
    (pkg / "commands" / "greet" / "__init__.py").write_text("")
    (pkg / "commands" / "greet" / "hello.py").write_text(
        textwrap.dedent(
            '''
            """A minimal action for runner tests."""
            from cac_core.command import Command


            class GreetHello(Command):
                state = {}

                def define_arguments(self, parser):
                    parser.add_argument("--name", default="world")
                    return parser

                def run(self, args):
                    GreetHello.state["name"] = args.name
                    GreetHello.state["verbose"] = getattr(args, "verbose", False)
                    return 0

                def execute(self, args):
                    return 0
            '''
        )
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    for mod in [m for m in sys.modules if m == "fakecli" or m.startswith("fakecli.")]:
        del sys.modules[mod]
    yield "fakecli"
    for mod in [m for m in sys.modules if m == "fakecli" or m.startswith("fakecli.")]:
        del sys.modules[mod]


class TestDiscovery:
    """Filesystem discovery helpers."""

    def test_discover_commands_and_actions(self, fake_pkg):
        pkg = importlib.import_module(fake_pkg)
        commands_dir = os.path.join(os.path.dirname(pkg.__file__), "commands")
        assert cli._discover_commands(commands_dir) == ["greet"]
        assert cli._discover_actions(os.path.join(commands_dir, "greet")) == ["hello"]

    def test_discover_missing_dir_is_empty(self, tmp_path):
        assert cli._discover_commands(str(tmp_path / "nope")) == []
        assert cli._discover_actions(str(tmp_path / "nope")) == []

    def test_discover_actions_skips_private_modules(self, tmp_path):
        command_dir = tmp_path / "cmd"
        command_dir.mkdir()
        (command_dir / "__init__.py").write_text("")
        (command_dir / "_helpers.py").write_text("")
        (command_dir / "_base.py").write_text("")
        (command_dir / "notes.txt").write_text("")
        (command_dir / "show.py").write_text("")
        (command_dir / "create.py").write_text("")
        # Only public .py modules are actions; private/support modules are skipped.
        assert cli._discover_actions(str(command_dir)) == ["create", "show"]


class TestRun:
    """End-to-end dispatch through the runner."""

    def test_dispatch_invokes_action_run(self, fake_pkg, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["fakecli", "greet", "hello", "--name", "bob"])
        code = cli.run(package=fake_pkg, prog="fakecli", description="x")
        assert code == 0
        from fakecli.commands.greet.hello import GreetHello

        assert GreetHello.state.get("name") == "bob"

    def test_missing_subcommand_exits(self, fake_pkg, monkeypatch):
        # argparse enforces the required subcommand and exits non-zero.
        monkeypatch.setattr(sys, "argv", ["fakecli"])
        with pytest.raises(SystemExit):
            cli.run(package=fake_pkg, prog="fakecli")

    def test_verbose_accepted_before_subcommand(self, fake_pkg, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["fakecli", "--verbose", "greet", "hello"])
        assert cli.run(package=fake_pkg, prog="fakecli") == 0
        from fakecli.commands.greet.hello import GreetHello

        assert GreetHello.state.get("verbose") is True

    def test_verbose_accepted_after_subcommand(self, fake_pkg, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["fakecli", "greet", "hello", "--verbose"])
        assert cli.run(package=fake_pkg, prog="fakecli") == 0
        from fakecli.commands.greet.hello import GreetHello

        assert GreetHello.state.get("verbose") is True

    def test_verbose_absent_defaults_false(self, fake_pkg, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["fakecli", "greet", "hello"])
        assert cli.run(package=fake_pkg, prog="fakecli") == 0
        from fakecli.commands.greet.hello import GreetHello

        assert GreetHello.state.get("verbose") is False


class TestActionSetupIsolation:
    """A broken action module is logged and skipped, not fatal to the CLI."""

    def _greet_dir(self, tmp_path):
        return tmp_path / "fakecli" / "commands" / "greet"

    def test_missing_class_is_skipped(self, fake_pkg, tmp_path, monkeypatch):
        # Module present but no matching {Command}{Action} class -> warned, skipped.
        (self._greet_dir(tmp_path) / "oops.py").write_text(
            "class WrongName:\n    pass\n"
        )
        monkeypatch.setattr(sys, "argv", ["fakecli", "greet", "hello", "--name", "z"])
        # The good action still dispatches despite the bad sibling module.
        assert cli.run(package=fake_pkg, prog="fakecli") == 0
        from fakecli.commands.greet.hello import GreetHello

        assert GreetHello.state.get("name") == "z"

    def test_setup_error_is_isolated(self, fake_pkg, tmp_path, monkeypatch):
        # define_arguments raising during setup must not abort the whole CLI.
        (self._greet_dir(tmp_path) / "boom.py").write_text(
            textwrap.dedent(
                """
                from cac_core.command import Command


                class GreetBoom(Command):
                    def define_arguments(self, parser):
                        raise RuntimeError("kaboom")

                    def execute(self, args):
                        return 0
                """
            )
        )
        monkeypatch.setattr(sys, "argv", ["fakecli", "greet", "hello"])
        assert cli.run(package=fake_pkg, prog="fakecli") == 0

    def test_import_error_is_isolated(self, fake_pkg, tmp_path, monkeypatch):
        # A module that fails to import must not abort the whole CLI.
        (self._greet_dir(tmp_path) / "badimport.py").write_text(
            "import a_module_that_does_not_exist_xyz  # noqa\n"
        )
        monkeypatch.setattr(sys, "argv", ["fakecli", "greet", "hello"])
        assert cli.run(package=fake_pkg, prog="fakecli") == 0

    def test_missing_argcomplete_is_graceful(self, fake_pkg, monkeypatch):
        # The runner degrades to no completion (not a crash) when argcomplete
        # is not installed.
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "argcomplete":
                raise ImportError("no argcomplete")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        monkeypatch.setattr(sys, "argv", ["fakecli", "greet", "hello"])
        assert cli.run(package=fake_pkg, prog="fakecli") == 0

    def test_command_run_exception_returns_one(self, fake_pkg, tmp_path, monkeypatch):
        # An exception escaping a command's own run() is caught by the runner.
        (self._greet_dir(tmp_path) / "crash.py").write_text(
            textwrap.dedent(
                """
                from cac_core.command import Command


                class GreetCrash(Command):
                    def define_arguments(self, parser):
                        return parser

                    def run(self, args):
                        raise RuntimeError("boom in run")

                    def execute(self, args):
                        return 0
                """
            )
        )
        monkeypatch.setattr(sys, "argv", ["fakecli", "greet", "crash"])
        assert cli.run(package=fake_pkg, prog="fakecli") == 1


class TestMakeMain:
    """make_main wraps run() as a console-script entry point."""

    def test_success_does_not_exit(self, fake_pkg, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["fakecli", "greet", "hello"])
        main = cli.make_main(fake_pkg, "fakecli", "desc")
        # A successful run returns None (no SystemExit).
        assert main() is None

    def test_failure_exits_nonzero(self, fake_pkg, tmp_path, monkeypatch):
        (tmp_path / "fakecli" / "commands" / "greet" / "crash.py").write_text(
            textwrap.dedent(
                """
                from cac_core.command import Command


                class GreetCrash(Command):
                    def define_arguments(self, parser):
                        return parser

                    def run(self, args):
                        raise RuntimeError("boom")

                    def execute(self, args):
                        return 0
                """
            )
        )
        monkeypatch.setattr(sys, "argv", ["fakecli", "greet", "crash"])
        main = cli.make_main(fake_pkg, "fakecli", "desc")
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    def test_prog_defaults_to_argv0_basename(self, fake_pkg, monkeypatch):
        # prog omitted -> derived from sys.argv[0]; should still run cleanly.
        monkeypatch.setattr(sys, "argv", ["/usr/local/bin/fakecli", "greet", "hello"])
        main = cli.make_main(fake_pkg)
        assert main() is None
