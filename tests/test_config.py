import unittest
from unittest.mock import patch, mock_open
import os
import yaml
from cac_core.config import load, save

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.module_name = 'test_module'
        self.default_config = {'key': 'value'}
        self.user_config_path = os.path.expanduser(f"~/.config/{self.module_name}/config.yaml")

    @patch('cac_core.config.os.path.exists')
    @patch('cac_core.config.os.makedirs')
    @patch('cac_core.config.open', new_callable=mock_open, read_data="key: value")
    @patch('cac_core.config.yaml.safe_load', return_value={'key': 'value'})
    @patch('cac_core.config.yaml.dump')
    def test_load_config_creates_user_config(self, mock_yaml_dump, mock_yaml_safe_load, mock_open, mock_makedirs, mock_path_exists):
        mock_path_exists.side_effect = lambda path: path != self.user_config_path

        config = load(self.module_name, self.default_config)

        mock_makedirs.assert_called_once_with(os.path.dirname(self.user_config_path), exist_ok=True)
        mock_open.assert_called_with(self.user_config_path, 'r')
        mock_yaml_dump.assert_called_once_with(self.default_config, mock_open())
        self.assertEqual(config['key'], 'value')
        self.assertEqual(config['config_file_path'], self.user_config_path)

    @patch('cac_core.config.os.path.exists', return_value=True)
    @patch('cac_core.config.open', new_callable=mock_open, read_data="key: value")
    @patch('cac_core.config.yaml.safe_load', return_value={'key': 'value'})
    def test_load_config_reads_existing_user_config(self, mock_yaml_safe_load, mock_open, mock_path_exists):
        config = load(self.module_name, self.default_config)

        mock_open.assert_called_with(self.user_config_path, 'r')
        mock_yaml_safe_load.assert_called_once_with(mock_open())
        self.assertEqual(config['key'], 'value')
        self.assertEqual(config['config_file_path'], self.user_config_path)

    @patch('cac_core.config.open', new_callable=mock_open)
    @patch('cac_core.config.yaml.dump')
    def test_save_config(self, mock_yaml_dump, mock_open):
        config = {'key': 'new_value'}
        save(self.module_name, config)

        mock_open.assert_called_with(self.user_config_path, 'w')
        mock_yaml_dump.assert_called_once_with(config, mock_open())

if __name__ == '__main__':
    unittest.main()
