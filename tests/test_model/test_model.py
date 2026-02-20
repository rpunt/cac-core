# pylint: disable=no-member

"""
Test suite for the Model class in the cac_core module.
"""

import copy

import pytest

import cac_core as cac


class TestModel:
    """Test suite for the Model class."""
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

        # Update via dict-style setter
        model["name"] = "Updated Project"
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
        model["name"] = "Modified Project"

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
        model.metadata["version"] = "2.0"
        assert model.metadata.version == "2.0"

    def test_setitem_existing_key(self, sample_data):
        """Test __setitem__ updates existing keys."""
        model = cac.model.Model(sample_data)
        model["status"] = "archived"
        assert model["status"] == "archived"
        assert model.status == "archived"

    def test_setitem_new_key(self, sample_data):
        """Test __setitem__ adds new keys."""
        model = cac.model.Model(sample_data)
        model["new_field"] = "new_value"
        assert model["new_field"] == "new_value"
        assert "new_field" in model.field_names
        assert "new_field" in model.keys()

    def test_getitem_missing_key(self, sample_data):
        """Test __getitem__ raises KeyError for missing keys."""
        model = cac.model.Model(sample_data)
        with pytest.raises(KeyError):
            _ = model["nonexistent"]

    def test_contains(self, sample_data):
        """Test 'in' operator."""
        model = cac.model.Model(sample_data)
        assert "name" in model
        assert "nonexistent" not in model

    def test_len(self, sample_data):
        """Test len() returns number of fields."""
        model = cac.model.Model(sample_data)
        assert len(model) == len(sample_data)

    def test_copy(self, sample_data):
        """Test shallow copy produces independent model."""
        model = cac.model.Model(sample_data)
        copied = copy.copy(model)

        assert copied.name == model.name
        assert copied is not model
        assert copied.data is not model.data
        assert copied.field_names is not model.field_names

        # Modifying copy should not affect original
        copied["name"] = "Copied Project"
        assert model.name == "Test Project"

    def test_deepcopy(self, sample_data):
        """Test deep copy produces fully independent model."""
        model = cac.model.Model(sample_data)
        deep = copy.deepcopy(model)

        assert deep.name == model.name
        assert deep is not model

        # Modifying nested data in deep copy should not affect original
        deep.metadata["version"] = "9.9"
        assert model.metadata.version == "1.0"

    def test_validate_base(self, sample_data):
        """Test base validate returns empty list."""
        model = cac.model.Model(sample_data)
        assert model.validate() == []

    def test_is_valid_base(self, sample_data):
        """Test base is_valid returns True."""
        model = cac.model.Model(sample_data)
        assert model.is_valid() is True

    def test_format_column(self, sample_data):
        """Test format_column stores formatter."""
        model = cac.model.Model(sample_data)
        formatter = lambda x: x.upper()
        model.format_column("name", formatter)
        assert model._formatters["name"] is formatter

    def test_to_json(self, sample_data):
        """Test JSON serialization."""
        import json
        model = cac.model.Model(sample_data)
        result = json.loads(model.to_json())
        assert result["name"] == "Test Project"
        assert result["metadata"]["version"] == "1.0"

    def test_repr(self, sample_data):
        """Test __repr__ output."""
        model = cac.model.Model(sample_data)
        r = repr(model)
        assert r.startswith("Model(")
        assert "..." in r  # sample_data has >3 keys

    def test_str(self, sample_data):
        """Test __str__ output."""
        model = cac.model.Model(sample_data)
        s = str(model)
        assert s.startswith("#<Model ")

    def test_remove_keys(self):
        """Test keys_to_remove filters fields."""
        data = {"name": "Test", "secret": "hidden", "key": "K1"}
        model = cac.model.Model(data, keys_to_remove=["secret"])
        assert "name" in model
        assert "secret" not in model

    def test_no_cross_instance_pollution(self):
        """Test that separate Model instances don't share field data."""
        m1 = cac.model.Model({"name": "first", "color": "red"})
        m2 = cac.model.Model({"age": 25, "city": "NYC"})
        assert m1.name == "first"
        assert m2.age == 25
        assert "age" not in m1.field_names
        assert "name" not in m2.field_names
