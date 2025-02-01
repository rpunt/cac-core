import os
import yaml

def load(module_name, default_config) -> dict:
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

    USER_CONFIG_PATH = os.path.expanduser(f"~/.config/{module_name}/config.yaml")
    USER_CONFIG_DIR = os.path.dirname(USER_CONFIG_PATH)

    # TODO: this does NOTHING right now, it's in the context of the module, not the caller
    # default_config = {}
    # default_config_dir = os.path.join(os.path.dirname(__file__), 'config')
    # default_config_file = os.path.join(default_config_dir, f"{module_name}.yaml")
    # if os.path.exists(default_config_file):
    #     with open(default_config_file, 'r') as f:
    #         default_config.update(yaml.safe_load(f))

    # if not os.path.exists(USER_CONFIG_DIR):
    os.makedirs(USER_CONFIG_DIR, exist_ok=True)

    if not os.path.exists(USER_CONFIG_PATH):
        with open(USER_CONFIG_PATH, 'w') as f:
            yaml.dump(default_config, f)

    # Re-read the user configuration file
    user_config = {}
    user_config['config_file_path'] = USER_CONFIG_PATH

    with open(USER_CONFIG_PATH, 'r') as f:
        user_config.update(yaml.safe_load(f))
    return user_config
