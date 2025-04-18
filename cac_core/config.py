# pylint: disable=line-too-long, broad-exception-caught

"""
Configuration module for the Command and Control (CAC) Core package.

This module provides functionality for loading, parsing, and accessing
configuration settings from various sources including environment variables
and configuration files. It supports multiple environments and hierarchical
configuration structures.
"""

import os
import sys
import yaml


class Config:
    """
    Configuration manager for CAC applications.

    This class handles loading and accessing configuration settings from
    various sources, with support for environment-specific configurations
    and overrides. It provides a centralized way to manage application settings.

    Attributes:
        config (dict): The loaded configuration settings
        env (str): The current environment (development, production, etc.)
    """

    def __init__(self, module_name) -> dict:
        self.config = {}
        self.config_file = os.path.expanduser(os.path.join("~", ".config", module_name, "config.yaml"))
        self.config_dir = os.path.dirname(self.config_file)
        self.module_name = module_name
        self.config = self.load(module_name)

        # Add each config key-value pair as an object attribute
        for key, value in self.config.items():
            setattr(self, key, value)

    def get(self, key: str, default=None) -> dict:
        """
        Get a configuration value by key.

        Args:
            key (str): The configuration key to retrieve
            default: The default value to return if the key is not found

        Returns:
            The configuration value or the default value if not found.
        """
        return self.config.get(key, default)

    def load(self, module_name) -> dict:
        """
        Load the configuration from YAML files.

        This function reads the default configuration from a YAML file named after the current module
        located in the 'config' directory. If the user configuration file at '~/.config/<module_name>/config.yaml'
        does not exist, it creates the necessary directories and writes the default configuration to this file.
        Finally, it reads and returns the user configuration.

        Returns:
            dict: The user configuration dictionary.

        Raises:
            OSError: If there is an error creating the directories or writing the configuration file.
        """
        # Try to load the default config from package directory
        default_config = self._load_default_config(module_name)

        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)

        # Create config file with default config if it doesn't exist
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f)

        # Read user configuration and merge with defaults
        config = {}
        config.update(default_config)
        config['config_file_path'] = self.config_file

        with open(self.config_file, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f)
            if user_config:
                config.update(user_config)

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
        module_path = sys.modules[module_name].__file__
        if not module_path:
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
                print(
                    f"Failed to load default config from {default_config_file}: {e}"
                )

        return default_config

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
