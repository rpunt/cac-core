# pylint: disable=broad-exception-caught

"""
Credential Management Module for CAC Applications.

This module provides a standardized interface for secure credential management
across CAC applications. It handles the complete credential lifecycle including:
- Retrieving credentials from system keychains
- Prompting users for credentials when not found
- Securely storing credentials for future use
- Deleting credentials when no longer needed

The module leverages the keyring library to provide cross-platform credential
storage, abstracting away platform-specific implementation details across
Windows, macOS, and Linux environments.

Features:
- Secure storage in system keychains (Windows Credential Locker, macOS Keychain, etc.)
- User-friendly prompting for missing credentials
- Consistent API for all credential operations
- Support for multiple credentials per application

Example:
    ```python
    from cac_core.credentialmanager import CredentialManager

    # Create credential manager for your application
    cred_manager = CredentialManager("my_application")

    # Get or prompt for an API token
    token = cred_manager.get_credential("user@example.com", "API token")

    # Use the retrieved credentials
    api_client.authenticate(cred_manager.username, token)

    # Store a credential without prompting
    cred_manager.set_credential("service_account", "api_key_value", "Service API Key")

    # Remove credentials when no longer needed
    cred_manager.delete_credential("old_account@example.com")
    ```
"""

import getpass
import keyring


class CredentialManager:
    """
    Manages secure credential storage and retrieval using system keychains.

    This class provides a simplified interface for working with credentials,
    handling both retrieval from system keychains and prompting users for input
    when credentials are not already stored. It uses the keyring library for
    secure storage across different operating systems.

    Attributes:
        module_name (str): The name of the module using this credential manager
        username (str): The username associated with the stored credentials
        credential (str): The credential (password/token) retrieved from keychain

    Example:
        ```python
        cred_mgr = CredentialManager("my_app")

        # Get a credential (will prompt if not found)
        api_key = cred_mgr.get_credential("user@example.com", "API key")

        # Set a credential explicitly
        cred_mgr.set_credential("user@example.com", "secret_token", "GitHub Token")
        ```
    """

    def __init__(self, module_name):
        """
        Initialize the credential manager.

        Args:
            module_name (str): The name of the module using this credential manager
        """
        self.module_name = module_name
        self.username = None
        self.credential = None

    def get_credential(self, username, description="credential", prompt=True):
        """
        Retrieve a credential from the system keychain.

        If the credential is not found and prompt is True, the user will be
        prompted to enter it, and it will be stored in the keychain.

        Args:
            username (str): The username associated with the credential
            description (str): Description of the credential for prompts
            prompt (bool): Whether to prompt for credential if not found

        Returns:
            str: The retrieved credential string or None if not found and not prompted
        """
        # Store username for reference
        self.username = username

        # Try to get credential from keychain
        credential_string = keyring.get_password(self.module_name, username)

        # If not found and prompting is enabled
        if not credential_string and prompt:
            print(f"{description} not found for {username}; please enter it now")
            print(f"Enter your {description}:")
            credential_string = getpass.getpass()

            if credential_string:
                # Store in keychain
                self.set_credential(username, credential_string, description)

        # Store for reference
        self.credential = credential_string
        return credential_string

    def set_credential(self, username, credential_string, description="credential"):
        """
        Store a credential in the system keychain.

        Args:
            username (str): The username associated with the credential
            credential_string (str): The credential to store
            description (str): Description of the credential (for logging)

        Returns:
            bool: True if credential was successfully stored
        """
        try:
            keyring.set_password(self.module_name, username, credential_string)
            self.username = username
            self.credential = credential_string
            return True
        except Exception as e:
            print(f"Failed to store {description} for {username}: {str(e)}")
            return False

    def delete_credential(self, username):
        """
        Delete a credential from the system keychain.

        Args:
            username (str): The username associated with the credential to delete

        Returns:
            bool: True if credential was successfully deleted
        """
        try:
            keyring.delete_password(self.module_name, username)
            if self.username == username:
                self.credential = None
            return True
        except Exception as e:
            print(f"Failed to delete credential for {username}: {str(e)}")
            return False
