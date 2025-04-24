# pylint: disable=line-too-long

"""
placeholder docstring
"""

import json
from contextlib import redirect_stdout
from io import StringIO

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

    def test_external_call(self, sample_models):
        """Test external call option returns data instead of printing."""
        output = cac.output.Output({"output": "json", "external_call": "true"}) # , external_call=True)
        result = output.print_models(sample_models)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Test Project"
