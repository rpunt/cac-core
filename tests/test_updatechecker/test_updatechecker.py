#!/usr/bin/env python
"""
Tests for the updatechecker module.

These tests verify that the UpdateChecker correctly checks for package updates,
handles various error conditions gracefully, and properly notifies users.
"""

import json
import logging
import os
import tempfile
from datetime import datetime, timedelta
import importlib.metadata
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import requests
from packaging.version import parse as parse_version

from cac_core.updatechecker import UpdateChecker, check_package_for_updates


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for update data files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def mock_update_checker(temp_data_dir):
    """Create an UpdateChecker with a temp directory."""
    with patch('cac_core.updatechecker.UpdateChecker._load_update_data') as mock_load,\
        patch('importlib.metadata.version', return_value="1.0.0"),\
        patch('cac_core.updatechecker.logger.warning'):  # Add this
        mock_load.return_value = {
            "last_check": None,
            "latest_version": None,
            "current_version": "1.0.0"
        }

        checker = UpdateChecker("test-package")
        checker.data_dir = temp_data_dir
        checker.data_file = temp_data_dir / "test-package_update.json"
        checker.current_version = "1.0.0"

        yield checker


class TestUpdateChecker:
    """Test suite for the UpdateChecker class."""

    def test_initialization(self):
        """Test that the UpdateChecker initializes correctly."""
        with patch('importlib.metadata.version', return_value="1.0.0"),\
            patch('cac_core.updatechecker.logger.warning') as mock_warning:  # Add this line
            checker = UpdateChecker("test-package")
            assert checker.package_name == "test-package"
            assert checker.current_version == "1.0.0"
            assert checker.source == "pypi"
            assert checker.update_url == "https://pypi.org/pypi/test-package/json"

            # Verify no warning was logged since we mocked the version
            mock_warning.assert_not_called()

    def test_github_source(self):
        """Test initialization with GitHub as the source."""
        with patch('importlib.metadata.version', return_value="1.0.0"):
            checker = UpdateChecker("test-package", source="github", repo="owner/repo")
            assert checker.source == "github"
            assert checker.repo == "owner/repo"
            assert checker.update_url == "https://api.github.com/repos/owner/repo/releases/latest"

    def test_package_not_found(self):
        """Test behavior when package is not found."""
        with patch('importlib.metadata.version', side_effect=importlib.metadata.PackageNotFoundError("test-package")),\
            patch('cac_core.updatechecker.logger.warning') as mock_warning:
            checker = UpdateChecker("nonexistent-package")
            assert checker.current_version == "0.0.0"

            # Verify warning was logged
            mock_warning.assert_called_once()
            assert "not found" in mock_warning.call_args[0][0]

    def test_load_update_data_new_file(self, mock_update_checker):
        """Test loading data when file doesn't exist."""
        # Instead of using __get__, which is causing the AttributeError,
        # directly call the original method from the UpdateChecker class
        original_method = UpdateChecker._load_update_data

        # Make the method instance-bound by manually passing 'self'
        def call_original():
            return original_method(mock_update_checker)

        # Save the mocked method to restore later
        mocked_method = mock_update_checker._load_update_data

        try:
            # Override with our wrapper to the original
            mock_update_checker._load_update_data = call_original

            # File doesn't exist yet, should return default data
            data = mock_update_checker._load_update_data()
            assert data["last_check"] is None
            assert data["latest_version"] is None
            assert data["current_version"] == "1.0.0"
        finally:
            # Restore the mock to avoid affecting other tests
            mock_update_checker._load_update_data = mocked_method

    def test_load_update_data_existing_file(self, temp_data_dir):
        """Test loading data from an existing file."""
        # Create a test file with data
        file_path = temp_data_dir / "test-package_update.json"
        test_data = {
            "last_check": datetime.now().isoformat(),
            "latest_version": "2.0.0",
            "current_version": "1.0.0"
        }

        with open(file_path, "w") as f:
            json.dump(test_data, f)

        # Initialize checker with test file
        with patch('importlib.metadata.version', return_value="1.0.0"):
            checker = UpdateChecker("test-package")
            checker.data_dir = temp_data_dir
            checker.data_file = file_path

            # Reset method to call real implementation
            checker._load_update_data = UpdateChecker._load_update_data.__get__(checker)

            data = checker._load_update_data()
            assert data["latest_version"] == "2.0.0"
            assert isinstance(data["last_check"], datetime)

    def test_save_update_data(self, mock_update_checker):
        """Test saving update data to file."""
        # Set up test data
        mock_update_checker.update_data = {
            "last_check": datetime.now(),
            "latest_version": "2.0.0",
            "current_version": "1.0.0"
        }

        # Get original method
        original_method = UpdateChecker._save_update_data

        # Make the method instance-bound
        def call_original():
            return original_method(mock_update_checker)

        # Save the mocked method
        mocked_method = mock_update_checker._save_update_data

        try:
            # Override with our wrapper
            mock_update_checker._save_update_data = call_original

            # Save the data
            mock_update_checker._save_update_data()

            # Verify file exists and contains expected data
            assert mock_update_checker.data_file.exists()

            with open(mock_update_checker.data_file, "r") as f:
                data = json.load(f)
                assert data["latest_version"] == "2.0.0"
                assert data["current_version"] == "1.0.0"
                # Check that datetime was serialized
                assert isinstance(data["last_check"], str)
        finally:
            # Restore the mock
            mock_update_checker._save_update_data = mocked_method

    def test_fetch_latest_version_pypi_success(self, mock_update_checker):
        """Test fetching the latest version from PyPI when successful."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "info": {"version": "2.0.0"}
        }

        with patch('requests.get', return_value=mock_response) as mock_get:
            version = mock_update_checker._fetch_latest_version()
            mock_get.assert_called_once_with(mock_update_checker.update_url, timeout=5)
            assert version == "2.0.0"

    def test_fetch_latest_version_github_success(self, mock_update_checker):
        """Test fetching the latest version from GitHub when successful."""
        mock_update_checker.source = "github"
        mock_update_checker.repo = "owner/repo"
        mock_update_checker.update_url = "https://api.github.com/repos/owner/repo/releases/latest"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tag_name": "v2.0.0"
        }

        with patch('requests.get', return_value=mock_response) as mock_get:
            version = mock_update_checker._fetch_latest_version()
            mock_get.assert_called_once_with(mock_update_checker.update_url, timeout=5)
            assert version == "2.0.0"

    def test_fetch_latest_version_request_error(self, mock_update_checker):
        """Test handling of request errors."""
        # Define a side effect function that raises an exception
        def request_error(*args, **kwargs):
            raise requests.RequestException("Connection error")

        # Patch requests.get to raise the RequestException
        with patch('requests.get', side_effect=request_error):
            # Previously stored version should be returned on error
            mock_update_checker.update_data["latest_version"] = "1.5.0"
            version = mock_update_checker._fetch_latest_version()
            assert version == "1.5.0"

            # Current version should be returned if no stored version
            mock_update_checker.update_data["latest_version"] = None
            version = mock_update_checker._fetch_latest_version()
            assert version == "1.0.0"

    def test_fetch_latest_version_json_error(self, mock_update_checker):
        """Test handling of JSON parse errors."""
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with patch('requests.get', return_value=mock_response):
            # Should handle JSON errors gracefully
            version = mock_update_checker._fetch_latest_version()
            assert version == "1.0.0"

    def test_check_for_updates_force(self, mock_update_checker):
        """Test forcing an update check."""
        with patch.object(mock_update_checker, '_fetch_latest_version', return_value="2.0.0") as mock_fetch:
            status = mock_update_checker.check_for_updates(force=True)
            mock_fetch.assert_called_once()
            assert status["latest_version"] == "2.0.0"
            assert status["update_available"] is True

    def test_check_for_updates_within_interval(self, mock_update_checker):
        """Test update check respects interval."""
        real_datetime = datetime.now() - timedelta(hours=1)
        mock_update_checker.update_data = {
            "last_check": real_datetime,
            "latest_version": "1.5.0",
            "current_version": "1.0.0"
        }

        mock_update_checker.check_interval = timedelta(hours=2)

        # Patch the get_update_status method to return consistent data
        with patch.object(mock_update_checker, '_fetch_latest_version') as mock_fetch, \
            patch.object(mock_update_checker, 'get_update_status', return_value={
                "latest_version": "1.5.0",
                "update_available": True
            }):

            status = mock_update_checker.check_for_updates(force=False)

            # Should not fetch when within interval
            mock_fetch.assert_not_called()
            assert status["latest_version"] == "1.5.0"

    def test_check_for_updates_interval_elapsed(self, mock_update_checker):
        """Test update check when interval has elapsed."""
        # Set last check to old time
        mock_update_checker.update_data["last_check"] = datetime.now() - timedelta(days=2)

        with patch.object(mock_update_checker, '_fetch_latest_version', return_value="2.0.0") as mock_fetch:
            status = mock_update_checker.check_for_updates(force=False)
            # Should fetch when interval elapsed
            mock_fetch.assert_called_once()
            assert status["latest_version"] == "2.0.0"

    def test_get_update_status(self, mock_update_checker):
        """Test getting update status with different versions."""
        # Test when update is available
        mock_update_checker.update_data["latest_version"] = "2.0.0"
        status = mock_update_checker.get_update_status()
        assert status["update_available"] is True

        # Test when current version is newer (dev version)
        mock_update_checker.current_version = "3.0.0"
        status = mock_update_checker.get_update_status()
        assert status["update_available"] is False

        # Test with invalid version
        mock_update_checker.update_data["latest_version"] = "invalid"
        with pytest.raises(Exception):
            mock_update_checker.get_update_status()

    def test_notify_if_update_available(self, mock_update_checker):
        """Test update notification using direct logger mocking."""
        with patch('cac_core.updatechecker.logger') as mock_logger:
            # Test with update available
            mock_update_checker.current_version = "1.0.0"
            mock_update_checker.update_data["latest_version"] = "2.0.0"

            # Make sure get_update_status returns the correct data
            with patch.object(mock_update_checker, 'get_update_status') as mock_get_status:
                mock_get_status.return_value = {
                    "update_available": True,
                    "current_version": "1.0.0",
                    "latest_version": "2.0.0"
                }

                result = mock_update_checker.notify_if_update_available()
                assert result is True
                # Check that info messages were logged for update available
                assert mock_logger.info.called

            # Reset mock before next test
            mock_logger.reset_mock()

            # Test with no update and quiet=False
            mock_update_checker.current_version = "3.0.0"
            mock_update_checker.update_data["latest_version"] = "2.0.0"

            # Mock get_update_status for the "up to date" case
            with patch.object(mock_update_checker, 'get_update_status') as mock_get_status:
                mock_get_status.return_value = {
                    "update_available": False,
                    "current_version": "3.0.0",
                    "latest_version": "2.0.0"
                }

                result = mock_update_checker.notify_if_update_available()
                assert result is False

            # Reset mock before next test
            mock_logger.reset_mock()

            # Test with no update and quiet=True
            # Mock get_update_status again
            with patch.object(mock_update_checker, 'get_update_status') as mock_get_status:
                mock_get_status.return_value = {
                    "update_available": False,
                    "current_version": "3.0.0",
                    "latest_version": "2.0.0"
                }

                result = mock_update_checker.notify_if_update_available(quiet=True)
                assert result is False
                # Verify no logs when quiet=True
                assert not mock_logger.info.called


def test_check_package_for_updates_convenience():
    """Test the convenience function."""
    with patch('cac_core.updatechecker.UpdateChecker') as MockUpdateChecker,\
        patch('cac_core.updatechecker.logger.warning'):  # Add this
        mock_instance = MockUpdateChecker.return_value
        mock_instance.check_for_updates.return_value = {
            "update_available": True,
            "current_version": "1.0.0",
            "latest_version": "2.0.0"
        }

        result = check_package_for_updates("test-package")

        MockUpdateChecker.assert_called_once_with("test-package")
        mock_instance.check_for_updates.assert_called_once_with(force=False)
        mock_instance.notify_if_update_available.assert_called_once_with(quiet=True)  # Updated: now defaults to quiet=True
        assert result["update_available"] is True

        # Test with explicit quiet=False
        MockUpdateChecker.reset_mock()
        mock_instance.reset_mock()

        result = check_package_for_updates("test-package", quiet=False)

        mock_instance.notify_if_update_available.assert_called_once_with(quiet=False)
        assert result["update_available"] is True


# if __name__ == "__main__":
#     pytest.main(["-xvs", __file__])
