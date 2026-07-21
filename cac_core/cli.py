"""
CLI runner for the Command and Control (CAC) Core package.

Provides the shared entry point every ``cac-*`` tool uses: ``run()`` discovers a
package's ``commands/`` tree, builds the nested ``argparse`` parser, wires up
shell completion, and dispatches to the selected action; ``make_main()`` wraps
that as a console-script callable.
"""

import argparse
import importlib
import logging
import os
import sys

from cac_core import logger as cac_logger


def _discover_commands(commands_dir):
    """Return the sorted command names found under ``commands_dir``.

    A command is any subdirectory that is a Python package (has an
    ``__init__.py``). This mirrors the filesystem-based discovery every
    ``cac-*`` CLI relies on -- commands need no explicit registration.
    """
    commands = []
    if not os.path.isdir(commands_dir):
        return commands
    for item in sorted(os.listdir(commands_dir)):
        item_path = os.path.join(commands_dir, item)
        if (
            os.path.isdir(item_path)
            and os.path.exists(os.path.join(item_path, "__init__.py"))
            and item != "__pycache__"
        ):
            commands.append(item)
    return commands


def _discover_actions(command_dir):
    """Return the sorted action names (public Python modules) under ``command_dir``.

    Only public ``.py`` modules are actions. Modules whose name starts with an
    underscore (``__init__.py``, ``_helpers.py``, ``_base.py``, ...) are treated
    as private support code and skipped, so a command package can colocate helper
    modules without them being mistaken for actions (and warned about) on every
    invocation.
    """
    actions = []
    if not os.path.isdir(command_dir):
        return actions
    for item in sorted(os.listdir(command_dir)):
        if not item.endswith(".py") or item.startswith("_"):
            continue
        actions.append(item[:-3])
    return actions


def _setup_logging(log, package, verbose):
    """Raise every ``<package>*`` logger to DEBUG when ``--verbose`` is set.

    The command and client modules each create their logger with an explicit
    INFO level and ``propagate=False``, so raising only the parent would not
    reach them -- set every logger in the package's namespace.
    """
    if not verbose:
        return
    log.setLevel(logging.DEBUG)
    logging.getLogger(package).setLevel(logging.DEBUG)
    for name, existing in logging.root.manager.loggerDict.items():
        if name.startswith(package) and isinstance(existing, logging.Logger):
            existing.setLevel(logging.DEBUG)


def run(package, prog, description=""):
    """Run a ``cac-*`` CLI: discover commands/actions, parse, and dispatch.

    This is the shared entry point for CAC command-line tools. It scans
    ``<package>/commands/`` for command packages and their action modules,
    builds a nested ``argparse`` parser (``<prog> <command> <action> [opts]``),
    wires up shell completion via ``argcomplete`` when available, then executes
    the selected action.

    Action classes are discovered by the ``{Command}{Action}`` naming
    convention (e.g. ``commands/issue/create.py`` -> ``IssueCreate``) and must
    implement ``define_arguments(parser)`` and ``execute(args)``.

    Args:
        package (str): Importable package name to scan (e.g. ``"cac_jira"``).
        prog (str): Program name shown in help/usage (e.g. ``"jira"``).
        description (str): Short description for the top-level parser.

    Returns:
        int: Exit code -- ``0`` on success, non-zero on failure. Callers are
        responsible for turning a non-zero return into ``sys.exit``.
    """
    log = cac_logger.new(f"{package}.cli")
    log.propagate = False

    pkg = importlib.import_module(package)
    if not pkg.__file__:
        log.error("Cannot locate the '%s' package on disk", package)
        return 1
    commands_dir = os.path.join(os.path.dirname(pkg.__file__), "commands")

    # Parent parser for arguments shared by every level of the command tree.
    # ``--verbose`` lives here (rather than only on the leaf action parsers) so
    # it is accepted before *or* after the subcommand -- ``jira --verbose issue
    # list`` and ``jira issue list --verbose`` both work. ``default=SUPPRESS`` is
    # essential: without it, the leaf subparser's default would overwrite a
    # ``--verbose`` set at a higher level (argparse's subparser-default clobber).
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--verbose",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Verbose output",
    )
    parser = argparse.ArgumentParser(
        prog=prog, description=description, parents=[parent_parser]
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = _discover_commands(commands_dir)
    log.debug("Discovered commands: %s", commands)

    command_subparsers = {}
    for command in commands:
        command_parser = subparsers.add_parser(
            command,
            help=f"{command.capitalize()}-related commands",
            parents=[parent_parser],
        )
        command_subparsers[command] = command_parser.add_subparsers(
            dest="action", required=True
        )

    # Build every action parser up front so completion and --help see the full
    # command tree. Failures for a single action are logged and skipped rather
    # than aborting the whole CLI.
    for command, subparser in command_subparsers.items():
        for action in _discover_actions(os.path.join(commands_dir, command)):
            module_path = f"{package}.commands.{command}.{action}"
            try:
                module = importlib.import_module(module_path)
                class_name = f"{command.capitalize()}{action.capitalize()}"
                action_class = getattr(module, class_name, None)
                if action_class is None:
                    log.warning(
                        "Class '%s' not found in module '%s'", class_name, module_path
                    )
                    continue
                action_instance = action_class()
                action_parser = subparser.add_parser(
                    action, help=f"{action} {command}", parents=[parent_parser]
                )
                action_instance.define_arguments(action_parser)
                action_parser.set_defaults(action_class=action_class)
            except ModuleNotFoundError:
                log.warning("Command module '%s' not found", module_path)
            except Exception as e:  # pylint: disable=broad-except
                log.warning("Error setting up %s %s: %s", command, action, e)

    # Shell-completion hook. Must run after the parser is fully built (so the
    # completer sees every command/action/flag) and before parse_args. Guarded
    # so a missing optional dependency degrades to no completion, not a crash.
    try:
        import argcomplete  # pylint: disable=import-outside-toplevel

        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    args = parser.parse_args()

    _setup_logging(log, package, getattr(args, "verbose", False))
    log.debug("Parsed arguments: %s", args)

    action_class = getattr(args, "action_class", None)
    if action_class is None:
        log.error(
            "No handler found for %s %s",
            getattr(args, "command", None),
            getattr(args, "action", None),
        )
        return 1
    if not callable(action_class):
        log.error("Invalid action class for %s %s", args.command, args.action)
        return 1

    action_instance = action_class()
    log.debug("Executing action: %s %s", args.command, args.action)
    try:
        exit_code = action_instance.run(args)
    except Exception as e:  # pylint: disable=broad-except
        # An error that escapes the command's own run() wrapper: include the
        # traceback under --verbose (debug) so it is diagnosable while keeping
        # normal output clean.
        log.error(
            "Error executing command: %s", e, exc_info=log.isEnabledFor(logging.DEBUG)
        )
        return 1

    return exit_code or 0


def make_main(package, prog=None, description=""):
    """Build a console-script ``main`` entry point for a CAC CLI.

    Returns a zero-argument callable suitable for ``[project.scripts]``. It runs
    the shared runner for ``package`` and translates a non-zero result into
    ``sys.exit`` so shells/CI observe the failure, while a success returns
    ``None`` (no ``SystemExit``) so direct callers -- e.g. tests -- aren't forced
    to handle it on the happy path.

    Args:
        package (str): Importable package to scan (e.g. ``"cac_jira"``).
        prog (str): Program name for help/usage. Defaults to the invoked script
            name (``sys.argv[0]``) when omitted.
        description (str): Short description for the top-level parser.

    Returns:
        Callable[[], None]: The ``main`` entry point.
    """

    def main():
        resolved_prog = prog or os.path.basename(sys.argv[0])
        exit_code = run(package=package, prog=resolved_prog, description=description)
        if exit_code:
            sys.exit(exit_code)

    return main
