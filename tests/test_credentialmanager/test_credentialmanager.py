"""
Test suite for the CredentialManager class in the cac_core module.
This module contains unit tests for the CredentialManager class, which
handles credential storage and retrieval using the keyring library.
"""

from unittest.mock import patch #, MagicMock
# import keyring
import pytest
# import getpass
import cac_core as cac


class TestCredentialManager:
    """Test suite for the CredentialManager class."""

    @pytest.fixture
    def credential_manager(self):
        """Create a CredentialManager instance for testing."""
        return cac.credentialmanager.CredentialManager("test_module")

    def test_init(self, credential_manager):
        """Test initialization of CredentialManager."""
        assert credential_manager.module_name == "test_module"
        assert credential_manager.username is None
        assert credential_manager.credential is None

    @patch("keyring.get_password")
    def test_get_credential_existing(self, mock_get_password, credential_manager):
        """Test retrieving an existing credential."""
        mock_get_password.return_value = "test_password"

        result = credential_manager.get_credential("test_user", "Test Password")

        mock_get_password.assert_called_once_with("test_module", "test_user")
        assert result == "test_password"
        assert credential_manager.username == "test_user"
        assert credential_manager.credential == "test_password"

    @patch("keyring.get_password")
    @patch("getpass.getpass")
    @patch("keyring.set_password")
    def test_get_credential_prompt(
        self, mock_set_password, mock_getpass, mock_get_password, credential_manager
    ):
        """Test prompting for a credential when not found."""
        mock_get_password.return_value = None
        mock_getpass.return_value = "new_password"

        result = credential_manager.get_credential("test_user", "Test Password")

        mock_get_password.assert_called_once_with("test_module", "test_user")
        mock_getpass.assert_called_once()
        mock_set_password.assert_called_once_with(
            "test_module", "test_user", "new_password"
        )
        assert result == "new_password"
        assert credential_manager.username == "test_user"
        assert credential_manager.credential == "new_password"

    @patch("keyring.get_password")
    def test_get_credential_not_found_no_prompt(
        self, mock_get_password, credential_manager
    ):
        """Test behavior when credential not found and prompting disabled."""
        mock_get_password.return_value = None

        result = credential_manager.get_credential(
            "test_user", "Test Password", prompt=False
        )

        mock_get_password.assert_called_once_with("test_module", "test_user")
        assert result is None
        assert credential_manager.username == "test_user"
        assert credential_manager.credential is None

    @patch("keyring.set_password")
    def test_set_credential_success(self, mock_set_password, credential_manager):
        """Test successful credential storage."""
        result = credential_manager.set_credential(
            "test_user", "test_password", "Test Password"
        )

        mock_set_password.assert_called_once_with(
            "test_module", "test_user", "test_password"
        )
        assert result is True
        assert credential_manager.username == "test_user"
        assert credential_manager.credential == "test_password"

    @patch("keyring.set_password")
    def test_set_credential_failure(self, mock_set_password, credential_manager):
        """Test handling of credential storage failure."""
        mock_set_password.side_effect = Exception("Storage error")

        with patch("builtins.print") as mock_print:
            result = credential_manager.set_credential("test_user", "test_password")

        mock_set_password.assert_called_once_with(
            "test_module", "test_user", "test_password"
        )
        mock_print.assert_called_once()
        assert "Failed to store" in mock_print.call_args[0][0]
        assert result is False

    @patch("keyring.delete_password")
    def test_delete_credential_success(self, mock_delete_password, credential_manager):
        """Test successful credential deletion."""
        credential_manager.username = "test_user"
        credential_manager.credential = "test_password"

        result = credential_manager.delete_credential("test_user")

        mock_delete_password.assert_called_once_with("test_module", "test_user")
        assert result is True
        assert credential_manager.credential is None

    @patch("keyring.delete_password")
    def test_delete_credential_failure(self, mock_delete_password, credential_manager):
        """Test handling of credential deletion failure."""
        mock_delete_password.side_effect = Exception("Deletion error")

        with patch("builtins.print") as mock_print:
            result = credential_manager.delete_credential("test_user")

        mock_delete_password.assert_called_once_with("test_module", "test_user")
        mock_print.assert_called_once()
        assert "Failed to delete" in mock_print.call_args[0][0]
        assert result is False
