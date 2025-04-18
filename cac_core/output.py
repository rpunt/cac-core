"""
Output module for the Command and Control (CAC) Core package.

This module provides the Output class which handles formatting and displaying
results from CAC operations. It supports multiple output formats including
tables and JSON, and adapts to different terminal environments.
"""

# pylint: disable=line-too-long

import json
import logging
import tabulate
import os

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

    def print_models(self, models, table_options=None):
        """
        Print models as a table or JSON depending on options.

        Args:
            models (list or object): Models to print
            table_options (dict, optional): Options for table formatting

        Returns:
            dict or None: Models as hash if external_call and suppress_output is set
        """
        if table_options is None:
            table_options = {}

        if self.opts.get('external_call') and (self.opts.get('suppress_output') is None or self.opts.get('suppress_output')):
            return self.__models_to_hash(models)

        if self.opts.get('json'):
            print(json.dumps([model.to_dict() for model in models] if isinstance(models, list) else models.to_dict()))
        else:
            models = list(models) if isinstance(models, list) else [models]

            if not models:
                self.logger.info('No results were found')
                return

            self.__resolve_models(models)
            self.__output_to_table(models, table_options)

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

    # def __column_options_from_models(self, models):
    #     keys = models[0].key_order if hasattr(models[0], 'key_order') else models[0].keys()
    #     column_options = models[0].column_options if hasattr(models[0], 'column_options') else {}

    #     return self._OutputTable__default_key_value_column_options()

    # def __default_key_value_column_options(self):
    #     return {
    #         'Key': {
    #             'align': 'right'
    #         },
    #         'Value': {
    #             'align': 'left'
    #         }
    #     }

    def __models_to_hash(self, models):
        return [model.to_dict() for model in models] if isinstance(models, list) else models.to_dict()

    def __models_to_json(self, models):
        return json.dumps(self.__models_to_hash(models))

    def __output_to_table(self, models, _table_options):
        if not models:
            return

        headers = models[0].keys()
        table_data = []
        for model in models:
            # Handle models that only have keys without values
            if hasattr(model, 'keys') and not hasattr(model, 'values'):
                table_data.append(model.keys())
            else:
                table_data.append(model.values())

        print(tabulate.tabulate(table_data, headers, tablefmt='pretty', stralign='left', numalign='right'))
        row_count = len(table_data)
        print(f"{row_count} {'row' if row_count == 1 else 'rows'}")

    def __resolve_models(self, models):
        for model in models:
            for k, v in model.items():
                if isinstance(v, dict):
                    model[k] = json.dumps(v)
                elif isinstance(v, list):
                    model[k] = ', '.join([json.dumps(x) if hasattr(x, 'to_dict') else str(x) for x in v])

    # def __terminal_width(self):
    #     try:
    #         return os.get_terminal_size().columns
    #     except OSError:
    #         return 155

# Example usage
if __name__ == "__main__":
    opts = {'json': False, 'external_call': False, 'suppress_output': False}
    output_table = Output(opts)
    models = [{'Key': 'example_key', 'Value': 'example_value'}]
    output_table.print_models(models)
