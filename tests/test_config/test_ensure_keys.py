"""
Tests for Config.ensure_keys() -- the shared first-run prompt helper.
"""

import pytest

from cac_core.config import Config


@pytest.fixture
def cfg(monkeypatch):
    """A Config with no disk/default/env interaction, empty to start."""
    monkeypatch.setattr(Config, "load", lambda self, module_name: {})
    monkeypatch.setattr(Config, "_load_env_vars", lambda self: None)
    monkeypatch.setattr(Config, "save", lambda self: True)
    return Config("testapp_ensure")


def test_prompts_and_stores_missing_key(cfg, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _p: "  https://x.example  ")
    wrote = cfg.ensure_keys(
        [("server", "URL: ", True, lambda v: v.replace("https://", ""))]
    )
    assert wrote is True
    assert cfg.get("server") == "x.example"
    # The convenience attribute is kept in sync.
    assert cfg.server == "x.example"


def test_skips_prompt_when_already_set(cfg, monkeypatch):
    cfg.set("server", "already")

    def _boom(_p):
        raise AssertionError("must not prompt for an already-set key")

    monkeypatch.setattr("builtins.input", _boom)
    assert cfg.ensure_keys([("server", "URL: ", True, None)]) is False
    assert cfg.get("server") == "already"


def test_argcomplete_skips_all_prompts(cfg, monkeypatch):
    monkeypatch.setenv("_ARGCOMPLETE", "1")

    def _boom(_p):
        raise AssertionError("must not prompt while completing")

    monkeypatch.setattr("builtins.input", _boom)
    assert cfg.ensure_keys([("server", "URL: ", True, None)]) is False
    assert cfg.get("server", "INVALID_DEFAULT") == "INVALID_DEFAULT"


def test_optional_empty_answer_not_saved(cfg, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _p: "")
    assert cfg.ensure_keys([("project", "Project: ", False, None)]) is False
    assert cfg.get("project", "INVALID_DEFAULT") == "INVALID_DEFAULT"


def test_required_empty_answer_is_saved(cfg, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _p: "")
    assert cfg.ensure_keys([("username", "User: ", True, None)]) is True
    assert cfg.get("username") == ""


def test_internal_state_key_not_clobbered(cfg, monkeypatch):
    # A config key named after Config's own internal attribute must be stored in
    # the dict but must NOT overwrite the instance attribute (self.config).
    monkeypatch.setattr("builtins.input", lambda _p: "hacked")
    original = cfg.config
    cfg.ensure_keys([("config", "Config: ", True, None)])
    assert cfg.get("config") == "hacked"
    assert cfg.config is original
    assert isinstance(cfg.config, dict)


def test_method_named_key_not_clobbered(cfg, monkeypatch):
    # A config key colliding with a method name must not overwrite the method.
    monkeypatch.setattr("builtins.input", lambda _p: "x")
    cfg.ensure_keys([("save", "Save: ", True, None)])
    assert callable(cfg.save)
    assert cfg.get("save") == "x"


def test_eof_on_prompt_degrades_gracefully(cfg, monkeypatch):
    # Non-interactive stdin (e.g. CI) makes input() raise EOFError; ensure_keys
    # must not crash -- it leaves keys at the sentinel and returns False.
    def _eof(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", _eof)
    assert cfg.ensure_keys([("server", "URL: ", True, None)]) is False
    assert cfg.get("server", "INVALID_DEFAULT") == "INVALID_DEFAULT"
