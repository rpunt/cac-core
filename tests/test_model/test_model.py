import pytest
import json
import cac_core as cac


class TestModel:
    def test_model_creation(self, sample_data):
        """Test creating a model from data."""
        model = cac.model.Model(sample_data)

        # Test attribute access
        assert model.name == "Test Project"
        assert model.key == "TEST"
        assert model.metadata.created == "2025-01-15"

    def test_model_attribute_update(self, sample_data):
        """Test updating model attributes."""
        model = cac.model.Model(sample_data)

        # Update via attribute setter
        getattr(model, "name=")("Updated Project")
        assert model.name == "Updated Project"

        # Check that internal data is updated
        assert model.data["name"] == "Updated Project"

    def test_model_dict_methods(self, sample_data):
        """Test dictionary-like methods."""
        model = cac.model.Model(sample_data)

        # Test keys() method
        keys = model.keys()
        assert "name" in keys
        assert "metadata" in keys

        # Test values() method
        values = model.values()
        assert "Test Project" in values

        # Test items() method
        items = dict(model.items())
        assert items["name"] == "Test Project"

        # Test get() method
        assert model.get("name") == "Test Project"
        assert model.get("nonexistent", "default") == "default"

    def test_model_to_dict(self, sample_data):
        """Test conversion to dictionary."""
        model = cac.model.Model(sample_data)

        # Modify one attribute
        getattr(model, "name=")("Modified Project")

        # Convert to dict
        result = model.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "Modified Project"
        assert result["metadata"]["version"] == "1.0"

    def test_nested_model(self, sample_data):
        """Test that nested dictionaries become models."""
        model = cac.model.Model(sample_data)

        assert isinstance(model.metadata, cac.model.Model)
        assert model.metadata.version == "1.0"

        # Update nested attribute
        getattr(model.metadata, "version=")("2.0")
        assert model.metadata.version == "2.0"
