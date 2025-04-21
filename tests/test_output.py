import unittest
from unittest.mock import patch, MagicMock
from cac_core.output import OutputTable

class TestOutputTable(unittest.TestCase):
    def setUp(self):
        self.opts = {'json': False, 'external_call': False, 'suppress_output': False}
        self.output_table = OutputTable(self.opts)

    @patch('cac_core.output.tabulate.tabulate')
    def test_print_models(self, mock_tabulate):
        models = [{'Key': 'example_key', 'Value': 'example_value'}]
        self.output_table.print_models(models)
        mock_tabulate.assert_called_once()

    def test_print_models_no_models(self):
        with patch.object(self.output_table.logger, 'info') as mock_logger_info:
            self.output_table.print_models([])
            mock_logger_info.assert_called_once_with('No results were found')

    def test_models_to_hash(self):
        models = [MagicMock(to_dict=lambda: {'Key': 'example_key', 'Value': 'example_value'})]
        result = self.output_table._OutputTable__models_to_hash(models)
        self.assertEqual(result, [{'Key': 'example_key', 'Value': 'example_value'}])

    def test_models_to_json(self):
        models = [MagicMock(to_dict=lambda: {'Key': 'example_key', 'Value': 'example_value'})]
        result = self.output_table._OutputTable__models_to_json(models)
        self.assertEqual(result, '[{"Key": "example_key", "Value": "example_value"}]')

    def test_default_key_value_column_options(self):
        result = self.output_table._OutputTable__default_key_value_column_options()
        self.assertEqual(result, {'Key': {'align': 'right'}, 'Value': {'align': 'left'}})

    @patch('cac_core.output.os.get_terminal_size')
    def test_terminal_width(self, mock_get_terminal_size):
        mock_get_terminal_size.return_value.columns = 100
        result = self.output_table._OutputTable__terminal_width()
        self.assertEqual(result, 100)

if __name__ == '__main__':
    unittest.main()
