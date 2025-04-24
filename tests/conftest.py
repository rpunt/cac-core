"""
Test fixtures for the CAC Core package.

This module contains pytest fixtures that are shared across multiple test modules
in the CAC Core test suite. It provides reusable test data and configurations
to ensure consistent test environments.

Fixtures defined here are automatically discovered by pytest and can be used
in any test function or class within the project without explicit imports.

Available fixtures:
- temp_config_file: Creates a temporary YAML configuration file for testing
- sample_data: Provides a consistent nested data structure for testing the Model class

Example:
    ```python
    def test_config_loading(temp_config_file):
        config = Config(config_file=temp_config_file)
        assert config.get('server') == 'https://test.example.com'

    def test_model_creation(sample_data):
        model = Model(sample_data)
        assert model.name == 'Test Project'
    ```
"""

import os
import tempfile
import pytest
import yaml


@pytest.fixture
def temp_config_file():
    """Creates a temporary config file for testing."""
    content = {
        "server": "https://test.example.com",
        "username": "test@example.com",
        "project": "TEST",
    }

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as temp:
        yaml.dump(content, temp)
        temp_path = temp.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_data():
    """Sample nested data structure for testing Model."""
    return {
        "name": "Test Project",
        "key": "TEST",
        "lead": "test@example.com",
        "status": "active",
        "components": ["Frontend", "Backend", "Database"],
        "metadata": {
            "created": "2025-01-15",
            "updated": "2025-04-20",
            "version": "1.0",
        },
    }
