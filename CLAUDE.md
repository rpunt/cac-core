# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cac-core is a Python foundational library for building CLI applications. It provides configuration management, credential storage, data modeling, output formatting, update checking, and an abstract command framework. Published to PyPI as `cac-core`.

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

**Config** (`config.py`): YAML-based configuration with a two-layer loading strategy — default config ships with the consuming module at `<module>/config/<module_name>.yaml`, user config lives at `~/.config/<module_name>/config.yaml`. User values override defaults. Environment variables override both, using the pattern `PREFIX_KEY` (e.g., `MY_APP_SERVER_PORT` overrides `server.port`). Supports dot-notation for nested key access/mutation.

**Model** (`model.py`): Dynamic data model that converts dicts into objects with attribute access. Nested dicts become nested Models automatically. Supports dict-like access (`model['key']`, `model.get()`), serialization (`to_dict()`, `to_json()`), copy/deepcopy, and key filtering via `remove_keys()`. Properties are created dynamically via `add_key()` using `property()` on the class.

**Command** (`command.py`): Abstract base class (uses `abc.ABCMeta`) that downstream commands must subclass. Requires implementing `define_arguments()` and `execute()`. Provides `safe_execute()` for exception-handling wrapper and `validate_args()` hook. Automatically adds `--output` and `--verbose` common arguments.

**Output** (`output.py`): Renders lists of Models as either formatted tables (via `tabulate`) or JSON.

**CredentialManager** (`credentialmanager.py`): Cross-platform credential storage using `keyring` (macOS Keychain, Windows Credential Locker, Linux keyrings). Prompts user via `getpass` when credentials are missing.

**UpdateChecker** (`updatechecker.py`): Checks PyPI or GitHub for newer versions with configurable intervals. Caches results in `~/.config/<package>/update.json`.

## Testing

Tests are organized in `tests/test_<module>/` directories. Shared fixtures are in `tests/conftest.py` (provides `temp_config_file` and `sample_data`). Python 3.12 is used in CI.
