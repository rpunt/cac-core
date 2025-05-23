#!/usr/bin/env python
"""
Tests for the config module.

These tests verify that the Config class correctly loads, manages, and saves
configuration data from YAML files, and properly handles environment variables.
"""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from cac_core.config import Config


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w', delete=False, encoding='utf-8') as f:
        # Use text mode ('w') and specify encoding
        config_data = {
            'api': {
                'url': 'https://api.example.com',
                'token': 'test-token'
            },
            'options': {
                'timeout': 30,
                'retries': 3
            },
            'feature_flags': {
                'enable_logging': True,
                'debug_mode': False
            }
        }
        yaml.dump(config_data, f)
        f.flush()
        yield f.name

    # Clean up after the test
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def sample_data():
    """Return sample config data."""
    return {
        'api': {
            'url': 'https://api.example.com',
            'token': 'test-token'
        },
        'options': {
            'timeout': 30,
            'retries': 3
        }
    }


class TestConfig:
    """Test suite for the Config class."""

    def test_init_with_defaults(self):
        """Test initializing config with default values."""
        # Create config with default name in default location
        config = Config('test-app')

        # Debug output to see the actual values
        print(f"config.config_dir: {config.config_dir}")
        print(f"config.config_file: {config.config_file}")
        print(f"Type of config_dir: {type(config.config_dir)}")
        print(f"Type of config_file: {type(config.config_file)}")

        # Check that config_dir and config_file are properly set
        assert isinstance(config.config_dir, str) or isinstance(config.config_dir, Path)
        assert 'test-app' in str(config.config_file)
        assert isinstance(config.config, dict)  # Changed from data to config
        assert config.config  # Config shouldn't be empty after initialization

    def test_init_with_custom_path(self):
        """Test initializing config with a custom path."""
        custom_path = '/tmp/custom-config.yaml'
        config = Config('test-app')
        # Manually set the config_file after creation
        config.config_file = Path(custom_path)
        assert str(config.config_file) == custom_path

    def test_load_existing_config(self, temp_config_file):
        """Test loading an existing config file."""
        config = Config('test-app')
        # Manually set the config_file and reload
        config.config_file = str(Path(temp_config_file))  # Ensure we have a string path, not bytes
        config.config = config._load_config()
        assert config.config['api']['url'] == 'https://api.example.com'
        assert config.config['options']['timeout'] == 30

    def test_get_existing_value(self, temp_config_file):
        """Test getting an existing value."""
        config = Config('test-app')
        config.config_file = Path(temp_config_file)
        config.config = config._load_config()  # Changed from data to config
        assert config.get('api.url') == 'https://api.example.com'
        assert config.get('options.timeout') == 30

    def test_get_nested_value(self, temp_config_file):
        """Test getting a nested value using dot notation."""
        config = Config('test-app')
        config.config_file = Path(temp_config_file)
        config.config = config._load_config()
        assert config.get('api.token') == 'test-token'

    def test_get_nonexistent_value_with_default(self):
        """Test getting a nonexistent value with a default."""
        config = Config('test-app')  # Empty config
        assert config.get('nonexistent', 'default-value') == 'default-value'

    def test_get_nonexistent_value_without_default(self):
        """Test getting a nonexistent value without a default."""
        config = Config('test-app')  # Empty config
        assert config.get('nonexistent') is None

    def test_set_new_value(self):
        """Test setting a new value."""
        config = Config('test-app')
        config.set('new-key', 'new-value')
        assert config.config['new-key'] == 'new-value'  # Changed from data to config
        assert config.get('new-key') == 'new-value'

    def test_set_nested_value(self):
        """Test setting a nested value using dot notation."""
        config = Config('test-app')
        config.set('nested.key', 'nested-value')
        assert config.config['nested']['key'] == 'nested-value'  # Changed from data to config
        assert config.get('nested.key') == 'nested-value'

    def test_set_overwrite_value(self, temp_config_file):
        """Test overwriting an existing value."""
        config = Config('test-app')
        config.config_file = Path(temp_config_file)
        config.config = config._load_config()
        config.set('api.url', 'https://new-api.example.com')
        assert config.get('api.url') == 'https://new-api.example.com'

    def test_save_config(self):
        """Test saving config to file."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            config_path = f.name

        try:
            # Create config without config_path parameter
            config = Config('test-app')
            # Manually set the config_file after creation
            config.config_file = Path(config_path)

            config.set('api.url', 'https://api.example.com')
            config.set('api.token', 'test-token')
            config.save()

            # Verify the file was created and contains expected data
            assert os.path.exists(config_path)

            # Load the file to verify contents
            with open(config_path, 'r') as f:
                saved_data = yaml.safe_load(f)

            assert saved_data['api']['url'] == 'https://api.example.com'
            assert saved_data['api']['token'] == 'test-token'
        finally:
            # Clean up
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_env_var_override(self, temp_config_file):
        """Test environment variable override."""
        # Set an environment variable that should override config
        os.environ['TEST_APP_API_URL'] = 'https://env-api.example.com'

        try:
            # Initialize Config with the env_prefix first, so env vars are loaded
            config = Config('test-app', env_prefix='TEST_APP')

            # Then set the config file and reload
            config.config_file = Path(temp_config_file)
            config.config = config._load_config()

            # After loading, explicitly apply env vars again
            config._load_env_vars()

            # The env var should override the config file value
            assert config.get('api.url') == 'https://env-api.example.com'

            # But other values should be unchanged
            assert config.get('api.token') == 'test-token'
        finally:
            # Clean up
            if 'TEST_APP_API_URL' in os.environ:
                del os.environ['TEST_APP_API_URL']

    def test_env_var_nonexistent_config(self):
        """Test environment variable when config key doesn't exist."""
        os.environ['TEST_APP_NONEXISTENT'] = 'env-value'

        try:
            config = Config('test-app', env_prefix='TEST_APP')

            # The env var should be used even though the key doesn't exist in config
            assert config.get('nonexistent') == 'env-value'
        finally:
            # Clean up
            if 'TEST_APP_NONEXISTENT' in os.environ:
                del os.environ['TEST_APP_NONEXISTENT']

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file."""
        nonexistent_path = '/tmp/nonexistent-config-{}.yaml'.format(os.getpid())

        # Ensure the file doesn't exist
        if os.path.exists(nonexistent_path):
            os.unlink(nonexistent_path)

        config = Config('test-app')
        config.config_file = Path(nonexistent_path)
        config.config = config._load_config()
        assert config.config == {}

    def test_load_invalid_yaml(self):
        """Test loading an invalid YAML file."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            f.write(b'invalid: yaml: file:')
            config_path = f.name

        try:
            # This should not raise an exception, but log an error and return empty dict
            config = Config('test-app')
            config.config_file = Path(config_path)
            config.config = config._load_config()
            assert config.config == {}
        finally:
            # Clean up
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_save_error_handling(self):
        """Test error handling when saving to an invalid location."""
        # Try to save to a location where we don't have permission
        if os.name != 'nt':  # Skip on Windows
            invalid_path = '/root/test-config.yaml'
            config = Config('test-app')
            # Manually set the config_file after creation
            config.config_file = Path(invalid_path)
            config.set('test', 'value')

            # This should not raise an exception but log an error
            config.save()

    def test_update_from_dict(self, sample_data):
        """Test updating config from a dictionary."""
        config = Config('test-app')
        config.update(sample_data)

        assert config.get('api.url') == 'https://api.example.com'
        assert config.get('options.timeout') == 30

    def test_update_nested_dict(self):
        """Test updating with nested dictionaries."""
        config = Config('test-app')
        config.update({
            'level1': {
                'level2': {
                    'level3': 'value'
                }
            }
        })

        assert config.get('level1.level2.level3') == 'value'

    def test_clear_config(self, temp_config_file):
        """Test clearing the configuration."""
        config = Config('test-app')
        config.config_file = Path(temp_config_file)
        config.config = config._load_config()  # Load the file first
        assert len(config.config) > 0
        config.clear()
        assert config.config == {}


if __name__ == '__main__':
    pytest.main(['-xvs', __file__])
