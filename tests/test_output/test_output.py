# pylint: disable=line-too-long

"""
Test suite for the Output class in the cac_core module.
"""

import argparse
import json
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import MagicMock

import pytest

import cac_core as cac


class TestOutput:
    """Test suite for the Output class."""

    @pytest.fixture
    def sample_models(self, sample_data):
        """Create sample models for testing output."""
        model1 = cac.model.Model(sample_data)
        model2 = cac.model.Model(
            {"name": "Second Project", "key": "SEC", "status": "inactive"}
        )
        return [model1, model2]

    def test_json_output(self, sample_models):
        """Test JSON output format."""
        output = cac.output.Output({"output": "json"})

        f = StringIO()
        with redirect_stdout(f):
            output.print_models(sample_models)

        captured = f.getvalue()

        parsed_json = json.loads(captured)

        assert len(parsed_json) == 2
        assert parsed_json[0]["name"] == "Test Project"
        assert parsed_json[1]["name"] == "Second Project"

    def test_table_output(self, sample_models):
        """Test table output format."""
        output = cac.output.Output({"output": "table"})

        f = StringIO()
        with redirect_stdout(f):
            output.print_models(sample_models)

        captured = f.getvalue()

        # Basic checks for table format
        assert "name" in captured
        assert "key" in captured
        assert "Test Project" in captured
        assert "Second Project" in captured
        assert "2 rows" in captured

    def test_get_param_none_dict_namespace_and_fallback(self):
        """_get_param handles None opts, argparse.Namespace, dict, and fallback."""
        assert cac.output.Output(None)._get_param("x", "d") == "d"

        ns = argparse.Namespace(output="json")
        assert cac.output.Output(ns)._get_param("output") == "json"

        assert cac.output.Output({"output": "json"})._get_param("output") == "json"

        # An opts value that is neither a dict nor has __dict__ -> fallback.
        assert cac.output.Output(42)._get_param("x", "d") == "d"

    def test_empty_table_logs_no_results(self):
        """An empty list in table mode logs a message and prints no table."""
        output = cac.output.Output({"output": "table"})
        output.logger = MagicMock()

        f = StringIO()
        with redirect_stdout(f):
            output.print_models([])

        output.logger.info.assert_called_once()
        assert "No results" in output.logger.info.call_args[0][0]
        assert "rows" not in f.getvalue()

    def test_single_model_renders_with_singular_row_count(self):
        """A single (non-list) model renders and reports '1 row'."""
        model = cac.model.Model({"name": "Solo", "key": "S"})
        output = cac.output.Output({"output": "table"})

        f = StringIO()
        with redirect_stdout(f):
            output.print_models(model)

        out = f.getvalue()
        assert "Solo" in out
        assert "1 row" in out

    def test_table_options_headers_exclude_formatters_width(self):
        """table_options honors custom headers, exclude, formatters, and widths."""
        models = [
            cac.model.Model({"id": 1, "name": "alice", "secret": "aaa"}),
            cac.model.Model({"id": 2, "name": "bob", "secret": "bbb"}),
        ]
        output = cac.output.Output({"output": "table"})
        opts = {
            "headers": {"name": "Full Name"},
            "exclude": ["secret"],
            "formatters": {"name": lambda v: v.upper()},
            "width": {"name": 20},
        }

        f = StringIO()
        with redirect_stdout(f):
            output.print_models(models, opts)

        out = f.getvalue()
        assert "Full Name" in out  # custom header applied
        assert "ALICE" in out  # formatter applied
        assert "secret" not in out and "aaa" not in out  # column excluded

    def test_table_flattens_nested_structures(self):
        """Lists and nested models are flattened for tabular display."""
        model = cac.model.Model(
            {
                "name": "proj",
                "tags": ["a", "b"],  # list -> comma-joined
                "meta": {"version": "1.0"},  # nested -> serialized
            }
        )
        output = cac.output.Output({"output": "table"})

        f = StringIO()
        with redirect_stdout(f):
            output.print_models([model])

        out = f.getvalue()
        assert "a, b" in out
        assert "version" in out
