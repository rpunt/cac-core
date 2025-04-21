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
