# pylint: disable=line-too-long, broad-exception-caught

"""
Configuration module for the CAC Core package.

This module provides functionality for loading, parsing, and accessing
configuration settings from various sources including environment variables
and configuration files. It supports multiple environments and hierarchical
configuration structures.
"""

import logging
import os
import sys
import yaml

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration manager for CAC applications.

    This class handles loading and accessing configuration settings from
    various sources, with support for environment-specific configurations
    and overrides. It provides a centralized way to manage application settings.

    By default, environment variables can override configuration values. The format
    is PREFIX_KEY, where PREFIX is the uppercase module name with hyphens replaced
    by underscores, and KEY is the configuration key with dots replaced by underscores.
    For example, for module 'my-app', the environment variable 'MY_APP_SERVER_PORT'
    would override the config key 'server.port'.

    Attributes:
        config (dict): The loaded configuration settings
        module_name (str): The name of the module this configuration belongs to
        env_prefix (str): The prefix used for environment variable overrides
        config_file (str): Path to the user's configuration file
    """

    def __init__(self, module_name, env_prefix=None):
        """
        Initialize a new Config instance.

        Args:
            module_name (str): The name of the module this configuration belongs to.
                               Used for locating default config files and as default env_prefix.
            env_prefix (str, optional): Prefix for environment variables that should override
                                       config values. If None, defaults to module_name converted
                                       to uppercase with hyphens replaced by underscores.
        """
        # Set instance variables first
        self.module_name = module_name
        # Default to module_name as prefix if None provided
        self.env_prefix = env_prefix if env_prefix is not None else module_name.upper().replace('-', '_')
        self.config_file = os.path.expanduser(os.path.join("~", ".config", module_name, "config.yaml"))
        self.config_dir = os.path.dirname(self.config_file)

        # Initialize config with empty dict, will be populated by load()
        self.config = {}

        # Now load the configuration
        self.config = self.load(module_name)

        # Load env vars after loading config
        self._load_env_vars()  # Always load env vars, since env_prefix now always has a value

        # Add each config key-value pair as an object attribute
        for key, value in self.config.items():
            setattr(self, key, value)

    def _load_env_vars(self):
        """
        Override configuration with environment variables.

        Environment variables with the specified prefix will override any matching
        configuration values. The format is PREFIX_KEY, with dots in the key replaced
        by underscores.

        For example, given the prefix "APP", the environment variable "APP_DATABASE_URL"
        would override the config key "database.url".
        """
        for env_key, env_value in os.environ.items():
            # Check if env var has our prefix
            if not env_key.startswith(f"{self.env_prefix}_"):
                continue

            # Remove prefix and convert to lowercase
            config_key = env_key[len(f"{self.env_prefix}_"):].lower()

            # Replace underscores with dots for nested keys
            config_key = config_key.replace("_", ".")

            # Set the value in our config
            self.set(config_key, env_value)

            # Also update any corresponding object attribute if it exists
            # This is important for maintaining consistency with the original attribute-setting logic
            if "." not in config_key and hasattr(self, config_key):
                setattr(self, config_key, env_value)

    def _load_config(self):
        """
        Load configuration from the specified config file.

        This is a simpler version of the load method that just loads from
        the current config_file without trying to copy default configs or
        create directories. Used when reloading config from a specific file.

        Returns:
            dict: The loaded configuration or empty dict if file not found or invalid
        """
        if not os.path.exists(self.config_file):
            return {}

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config or {}
        except Exception as e:
            # Using print since logger might not be configured yet
            print(f"Error loading config from {self.config_file}: {e}")
            return {}

    def get(self, key: str, default=None) -> any:
        """
        Get a configuration value by key.

        This method supports both top-level and nested configuration values using
        dot notation.

        Args:
            key (str): The configuration key to retrieve (e.g., 'api.url')
            default: The default value to return if the key is not found

        Returns:
            The configuration value or the default value if not found.
        """
        if '.' not in key:
            # Simple case: top-level key
            return self.config.get(key, default)

        # Handle nested keys
        parts = key.split('.')
        current = self.config

        # Navigate to the nested location
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                return default
            current = current[part]

        # Return the value at the final location
        return current.get(parts[-1], default)

    def set(self, key_path: str, value: any) -> None:
        """
        Set a configuration value using dot notation path.

        This method supports both top-level and nested configuration values using
        dot notation. For nested paths, it creates intermediate dictionaries as needed.

        Args:
            key_path (str): The dot-separated path to the config value (e.g., 'api.url', 'server.options.timeout')
            value (any): The value to set at the specified path

        Examples:
            >>> config.set('api.url', 'https://api.example.com')
            >>> config.set('debug', True)
            >>> config.set('server.timeout', 30)
        """
        if '.' not in key_path:
            # Simple case: top-level key
            self.config[key_path] = value
            return

        # Handle nested keys
        parts = key_path.split('.')
        current = self.config

        # Navigate to the nested location, creating dictionaries as needed
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        # Set the value at the final location
        current[parts[-1]] = value

    def load(self, module_name) -> dict:
        """
        Load configuration from default and user YAML files.

        The method performs the following steps:
        1. Loads default configuration from the module's config directory
        2. If user config doesn't exist at '~/.config/<module_name>/config.yaml':
           - Creates it using self.save() with default values
           - Returns the default configuration
        3. If user config exists:
           - Loads and merges it with default configuration
           - User values override default values for the same keys

        The resulting configuration includes a 'config_file_path' key with the
        path to the user's configuration file.

        Args:
            module_name: The name of the module to load configuration for

        Returns:
            dict: The merged configuration dictionary with defaults and user settings.

        Raises:
            OSError: If there is an error creating directories or writing the config file.

        Example:
            >>> config = Config('myapp')
            >>> config.load('myapp')  # Returns merged configuration
        """
        # Get default configuration
        default_config = self._load_default_config(module_name)

        # Create result config starting with defaults
        config = default_config.copy()

        # Add the config file path to the configuration
        config['config_file_path'] = self.config_file

        # Handle non-existent user config file
        if not os.path.exists(self.config_file):
            # Temporarily store default config and save it using self.save()
            temp_config = self.config  # Save current config (if any)
            self.config = default_config.copy()
            self.save()  # Use the existing save method to create the file
            self.config = temp_config  # Restore current config

            # Return the default config with file path added
            return config

        # Load and merge user configuration if it exists
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    config.update(user_config)
        except Exception as e:
            # Log the error but continue with defaults
            print(f"Error reading user config file {self.config_file}: {e}")
            # Note: logger may not be configured yet, so using print

        return config

    def _load_default_config(self, module_name):
        """
        Automatically load default config from the module's config directory.

        Args:
            module_name: Module name to load default config for

        Returns:
            dict: Default configuration or empty dict if not found
        """
        default_config = {}
        try:
            module_path = sys.modules[module_name].__file__
        except KeyError:
            # this exception mostly covers testing cases where there's no actual module in the call stack
            # print(f"Module {module_name} not found in sys.modules.")
            return default_config

        module_dir = os.path.dirname(module_path)
        default_config_dir = os.path.join(module_dir, "config")
        default_config_file = os.path.join(default_config_dir, f"{module_name}.yaml")

        if os.path.exists(default_config_file):
            try:
                with open(default_config_file, "r", encoding="utf-8") as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        default_config.update(loaded_config)
            except Exception as e:
                print(f"Failed to load default config from {default_config_file}: {e}")

        return default_config

    def save(self):
        """
        Save the current configuration to the config file.

        This method writes the current configuration dictionary back to the
        YAML file specified by the config_file attribute. It creates any
        necessary parent directories if they don't exist.

        Returns:
            bool: True if the save was successful, False otherwise

        Raises:
            None: Errors are caught and logged
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            # Write the config to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f)

            return True
        except (IOError, OSError) as e:
            # Log error but don't crash
            logger.error("Failed to save configuration to %s: %s", self.config_file, str(e))
            return False

    def clear(self):
        """
        Clear all configuration values.

        This method resets the configuration dictionary to an empty state.
        It does not affect the configuration file until save() is called.
        """
        self.config = {}

    def update(self, update_dict):
        """
        Update configuration with values from a dictionary.

        Args:
            update_dict (dict): Dictionary containing configuration values to update
        """
        self.config.update(update_dict)

    def validate_schema(self, schema):
        """
        Validates configuration against a JSON schema.

        Args:
            schema (dict): JSON schema to validate against

        Returns:
            tuple: (is_valid, errors)
        """
        try:
            import jsonschema # pylint: disable=import-outside-toplevel
            jsonschema.validate(self.config, schema)
            return True, []
        except jsonschema.exceptions.ValidationError as e:
            return False, [str(e)]
        except ImportError:
            print("jsonschema package not installed, skipping validation")
            return True, ["jsonschema not installed"]

    def __enter__(self):
        """Support for with statement: with Config() as config:"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context"""
        # Add any cleanup if needed
        pass  # pylint: disable=unnecessary-pass
