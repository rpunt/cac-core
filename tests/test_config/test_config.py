# import os
# import pytest
# import yaml
import cac_core as cac

class TestConfig:
    # def test_load_config_from_file(self, temp_config_file):
    #     """Test loading configuration from a file."""
    #     # Use the same namespace as in your fixture
    #     config = cac.config.Config("test_app")
    #     loaded_config = config.load(temp_config_file)

    #     assert loaded_config is not None
    #     assert loaded_config.get("server") == "https://test.example.com"
    #     assert loaded_config.get("username") == "test@example.com"

    def test_config_get_with_default(self):
        """Test get() method with default value."""
        config = cac.config.Config("test")
        config.config = {"server": "https://example.com"}

        assert config.get("server") == "https://example.com"
        assert config.get("nonexistent", "default") == "default"

    # def test_config_set(self):
    #     """Test set() method."""
    #     config = cac.config.Config("test")
    #     config.set("new_key", "new_value")
    #     assert config.get("new_key") == "new_value"

    # def test_environment_variable_override(self, monkeypatch):
    #     """Test environment variable overrides config."""
    #     config = cac.config.Config("test")
    #     config.config = {"server": "https://example.com"}

    #     # Set environment variable
    #     monkeypatch.setenv("TEST_SERVER", "https://env.example.com")

    #     # Environment variable should take precedence
    #     assert config.get("server") == "https://env.example.com"
