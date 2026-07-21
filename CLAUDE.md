# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cac-core is a Python foundational library for building CLI applications. It provides a shared CLI runner, an abstract command framework, configuration management, credential storage, data modeling, output formatting, and update checking. Published to PyPI as `cac-core`.

Downstream tools (e.g. `cac-jira`) are intentionally thin: they supply a `commands/` tree and a one-line `main` entry point, and inherit discovery, argument parsing, shell completion, dispatch, error-to-exit-code mapping, and first-run config prompts from here.

## Commands

```bash
# Install dependencies (uses uv as package manager)
uv pip install -e ".[dev]"

# Run all tests
uv run pytest

# Run tests with doctests
uv run pytest --doctest-modules

# Run a single test file
uv run pytest tests/test_config/test_config.py

# Run a single test
uv run pytest tests/test_config/test_config.py::TestConfig::test_method_name

# Lint
uv pip install -e ".[lint]"
# black, isort, pylint are configured as lint dependencies
```

## Architecture

All modules are exported from `cac_core/__init__.py` and are designed to be used by downstream CLI applications that depend on this library.

**CLI** (`cli.py`): The shared runner. `run(package, prog, description)` scans `<package>/commands/` for command packages and their public action modules (files not starting with `_`), builds the nested `argparse` parser (`<prog> <command> <action> [opts]`) using the `{Command}{Action}` class-naming convention, wires up `argcomplete`, then dispatches to the selected action's `run(args)`. `make_main(package, prog, description)` returns a zero-argument `main` callable for `[project.scripts]` that turns a non-zero result into `sys.exit`. A global `--verbose` is added to the shared parent parser with `default=argparse.SUPPRESS` so it is accepted before *or* after the subcommand without the leaf subparser clobbering it. (The legacy `CLI` class was removed — `run`/`make_main` are the entry points.)

**Config** (`config.py`): YAML-based configuration with a two-layer loading strategy — default config ships with the consuming module at `<module>/config/<module_name>.yaml`, user config lives at `~/.config/<module_name>/config.yaml`. User values override defaults. Environment variables override both, using the pattern `PREFIX_KEY` (e.g., `MY_APP_SERVER_PORT` overrides `server.port`). Supports dot-notation for nested key access/mutation. `ensure_keys(specs)` drives first-run prompts for missing keys and skips prompting during shell completion (`_ARGCOMPLETE` set) so tab-completion never hangs on `input()`.

**Model** (`model.py`): Dynamic data model that converts dicts into objects with attribute access. Nested dicts become nested Models automatically. Supports dict-like access (`model['key']`, `model.get()`), serialization (`to_dict()`, `to_json()`), copy/deepcopy, and key filtering via `remove_keys()`. Properties are created dynamically via `add_key()` using `property()` on the class.

**Command** (`command.py`): Abstract base class (uses `abc.ABCMeta`) that downstream commands must subclass. Requires implementing `define_arguments()` and `execute()`. Provides the `run(args)` template invoked by the runner: it calls `execute()` and maps any raised exception to a logged, non-zero exit code via `handle_exception()` (override this for domain-specific errors). `execute()` must return an `int` exit code or `None` (treated as `0`); any other return — including a `bool` — is treated as a failure and logged rather than passed to `sys.exit`. `define_common_arguments()` adds the `--output`/`--verbose` common arguments. `CommandError` is a lightweight exception type available for commands to raise. The logger is namespaced under the command's module (e.g. `cac_jira.commands.issue.show.IssueShow`) so the runner's package-prefixed `--verbose` handling reaches it.

**Output** (`output.py`): Renders lists of Models as either formatted tables (via `tabulate`) or JSON.

**CredentialManager** (`credentialmanager.py`): Cross-platform credential storage using `keyring` (macOS Keychain, Windows Credential Locker, Linux keyrings). Prompts user via `getpass` when credentials are missing.

**UpdateChecker** (`updatechecker.py`): Checks PyPI or GitHub for newer versions with configurable intervals. Caches results in `~/.config/<package>/update.json`.

## Testing

Tests are organized in `tests/test_<module>/` directories. Shared fixtures are in `tests/conftest.py` (provides `temp_config_file` and `sample_data`). Python 3.12 is used in CI.
