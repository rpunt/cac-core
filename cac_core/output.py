"""
Output module for the CAC Core package.

This module provides the Output class which handles formatting and displaying
results from CAC operations. It supports multiple output formats including
tables and JSON, and adapts to different terminal environments.
"""

# pylint: disable=line-too-long

import json
import logging
import tabulate

class ColumnFormatter:
    def __init__(self, key, formatter=None, header=None, width=None):
        self.key = key
        self.formatter = formatter or (lambda x: x)
        self.header = header or key
        self.width = width

class Output:
    """
    Handles the formatting and display of data in the CAC framework.

    This class provides functionality to output data as tables or JSON,
    with support for various formatting options and terminal width detection.
    It can also convert models to dictionaries for external API calls.

    Attributes:
        opts (dict): Options that control output behavior
        logger (Logger): Logger instance for output messages
    """

    def __init__(self, opts):
        self.opts = opts
        self.logger = self.__create_logger()

    def print_models(self, data_models, table_options=None):
        """
        Print models as a table or JSON based on output configuration.

        This method handles the display of model data in the format specified by the
        output options. For JSON output, it directly converts models to JSON without
        flattening complex structures. For table output, it flattens nested structures
        and formats data into a tabular display.

        Args:
            data_models (list or Model): Models to print. Can be a single Model instance
                or a list of Model instances.
            table_options (dict, optional): Options for table formatting with keys:
                - formatters: Dict mapping column names to formatter functions
                - headers: Custom column headers mapping
                - width: Fixed column width settings
                - exclude: Columns to exclude from output

        Returns:
            None: If output is displayed to console
            dict: Models as dictionary if external_call and suppress_output are set

        Examples:
            >>> output = Output({'output': 'table'})
            >>> output.print_models([model1, model2])

            >>> output = Output({'output': 'json'})
            >>> output.print_models(model)
        """
        if table_options is None:
            table_options = {}

        if self.opts.get("external_call", False): # and (self.opts.get("suppress_output", False)):
            return self.__models_to_dict(data_models)

        if self.opts['output'] == 'json':
            self.__models_to_json(data_models)

        if self.opts['output'] == 'table':
            # For table output, resolve models (flatten complex structures)
            data_models = list(data_models) if isinstance(data_models, list) else [data_models]
            if not data_models:
                self.logger.info('No results were found')
                return
            self.__resolve_models(data_models)
            self.__output_to_table(data_models, table_options)

    def __create_logger(self):
        logger = logging.getLogger("OutputTable")
        logger.setLevel(logging.INFO)
        sh = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] (%(processName)s %(threadName)s) %(module)s:%(lineno)d: %(message)s"
        )
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        return logger

    def __models_to_dict(self, data_models):
        return (
            [model.to_dict() for model in data_models]
            if isinstance(data_models, list)
            else data_models.to_dict()
        )

    def __models_to_json(self, data_models):
        print(json.dumps(self.__models_to_dict(data_models)))

    def __output_to_table(self, data_models, _table_options):
        if not data_models:
            return

        # Get ordered headers from first model
        headers = list(data_models[0].keys())

        table_data = []
        for model in data_models:
            # For each model, extract values in the same order as headers
            row = [model.get(key) for key in headers]
            table_data.append(row)

        print(tabulate.tabulate(table_data, headers, tablefmt='pretty', stralign='left', numalign='right'))
        row_count = len(table_data)
        print(f"{row_count} {'row' if row_count == 1 else 'rows'}")

    def __resolve_models(self, data_models):
        for model in data_models:
            for k, v in model.items():
                if isinstance(v, dict):
                    getattr(model, f"{k}=")(json.dumps(v))
                elif isinstance(v, list):
                    formatted_list = ', '.join([json.dumps(x) if hasattr(x, 'to_dict') else str(x) for x in v])
                    getattr(model, f"{k}=")(formatted_list)

# Example usage
if __name__ == "__main__":
    opts = {'json': False, 'external_call': False, 'suppress_output': False}
    output_table = Output(opts)
    models = [{'Key': 'example_key', 'Value': 'example_value'}]
    output_table.print_models(models)
