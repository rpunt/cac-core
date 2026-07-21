#!/usr/bin/env python
# pylint: disable=protected-access

"""
Additional Config tests covering environment-variable coercion, attribute
exposure, deep merging, default-config discovery, and schema validation.
"""

import builtins
import sys
import textwrap

import pytest

from cac_core.config import Config


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Redirect ~/.config writes into a temp dir so tests never touch $HOME."""
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


class TestEnvCoercion:
    """Env overrides are coerced to the existing value's type (config.py)."""

    def test_int_bool_float_coercion(self, monkeypatch):
        monkeypatch.setenv("TESTCOERCE_TIMEOUT", "45")
        monkeypatch.setenv("TESTCOERCE_DEBUG", "yes")
        monkeypatch.setenv("TESTCOERCE_RATIO", "1.5")
        config = Config("testcoerce", env_prefix="TESTCOERCE")
        # Seed typed values, then re-apply env overrides.
        config.config = {"timeout": 30, "debug": False, "ratio": 0.1}
        config._load_env_vars()

        assert config.get("timeout") == 45
        assert isinstance(config.get("timeout"), int)
        assert config.get("debug") is True
        assert config.get("ratio") == 1.5

    def test_bad_numeric_value_falls_back_to_string(self, monkeypatch):
        monkeypatch.setenv("TESTCOERCE_TIMEOUT", "not-a-number")
        config = Config("testcoerce", env_prefix="TESTCOERCE")
        config.config = {"timeout": 30}
        config._load_env_vars()
        # Coercion fails -> the raw string is kept rather than crashing.
        assert config.get("timeout") == "not-a-number"

    def test_literal_underscore_key_matched(self, monkeypatch):
        # A key that legitimately contains underscores is matched literally
        # rather than being split into a nested "log.level" path.
        monkeypatch.setenv("TESTCOERCE_LOG_LEVEL", "9")
        config = Config("testcoerce", env_prefix="TESTCOERCE")
        config.config = {"log_level": 1}
        config._load_env_vars()
        assert config.get("log_level") == 9


class TestAttributeExposure:
    """Config keys are exposed as attributes unless they shadow the API."""

    def test_colliding_key_is_not_exposed(self, monkeypatch):
        # Force a config whose keys include one that collides with a method.
        monkeypatch.setattr(
            Config, "load", lambda self, module_name: {"save": "x", "server": "y"}
        )
        monkeypatch.setattr(Config, "_load_env_vars", lambda self: None)
        config = Config("testexpose")

        # "save" collides with the method -> not overwritten; still callable.
        assert callable(config.save)
        assert config.get("save") == "x"
        # A non-colliding key is exposed as an attribute.
        assert config.server == "y"


class TestDeepMerge:
    """_deep_merge merges nested dicts key-by-key (config.py)."""

    def test_nested_override_preserves_siblings(self):
        base = {"a": {"x": 1, "y": 2}, "b": 5}
        override = {"a": {"y": 9, "z": 3}}
        merged = Config._deep_merge(base, override)
        assert merged == {"a": {"x": 1, "y": 9, "z": 3}, "b": 5}
        # Input dicts are not mutated.
        assert base == {"a": {"x": 1, "y": 2}, "b": 5}

    def test_scalar_replaces_dict(self):
        merged = Config._deep_merge({"a": {"x": 1}}, {"a": 7})
        assert merged == {"a": 7}


class TestDefaultConfig:
    """Default config ships with the module at <module>/config/<module>.yaml."""

    def test_loads_default_config_from_module(self, tmp_path, monkeypatch):
        pkg = tmp_path / "tmpcfgmod"
        (pkg / "config").mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (pkg / "config" / "tmpcfgmod.yaml").write_text(
            textwrap.dedent(
                """
                server: default.example
                level: 5
                """
            )
        )
        monkeypatch.syspath_prepend(str(tmp_path))
        sys.modules.pop("tmpcfgmod", None)
        import tmpcfgmod  # noqa: F401  (import needed so Config can find __file__)

        try:
            config = Config("tmpcfgmod")
            assert config.get("server") == "default.example"
            assert config.get("level") == 5
        finally:
            sys.modules.pop("tmpcfgmod", None)


class TestContextManager:
    """Config supports use as a context manager."""

    def test_enter_returns_self_and_exit_is_clean(self):
        config = Config("testctx")
        with config as ctx:
            assert ctx is config
        # Exiting must not raise.


class TestValidateSchema:
    """validate_schema degrades gracefully and validates when available."""

    def test_without_jsonschema(self, monkeypatch):
        # Force the ImportError path regardless of whether jsonschema is present.
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("no jsonschema")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        config = Config("testschema")
        ok, errors = config.validate_schema({"type": "object"})
        assert ok is True
        assert "jsonschema not installed" in errors[0]

    def test_valid_and_invalid(self):
        pytest.importorskip("jsonschema")
        config = Config("testschema")
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        }
        config.config = {"name": "ok"}
        assert config.validate_schema(schema) == (True, [])

        config.config = {}
        ok, errors = config.validate_schema(schema)
        assert ok is False
        assert errors
