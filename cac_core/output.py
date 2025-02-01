import json
import logging
import tabulate
import os

class OutputTable:
    def __init__(self, opts):
        self.opts = opts
        self.logger = self.__create_logger()

    def print_models(self, models, table_options=None):
        """
        Print the given models in a tabular format.

        This method converts the given models to a list, resolves any nested models,
        and prints them in a table format using the tabulate module. If no models are
        provided, it logs an informational message.

        Args:
            models (list): A list of model instances to be printed.
            table_options (dict, optional): A dictionary of options for table formatting.
                Defaults to None.

        Returns:
            None
        """
        if table_options is None:
            table_options = {}

        # if self.opts.get('external_call') and (self.opts.get('suppress_output') is None or self.opts.get('suppress_output')):
        #     return self.__models_to_hash(models)
        # if self.opts.get('json'):
        #     return self.__models_to_json(models)

        models = list(models)

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

    def __column_options_from_models(self, models):
        keys = models[0].key_order if hasattr(models[0], 'key_order') else models[0].keys()
        column_options = models[0].column_options if hasattr(models[0], 'column_options') else {}

        # if not column_options and len(keys) == 2 and 'Key' in keys and 'Value' in keys:
        #     return self._OutputTable__default_key_value_column_options()
        # else:
        #     return {key: {} for key in keys}
        return self._OutputTable__default_key_value_column_options()

    def __default_key_value_column_options(self):
        return {
            'Key': {
                'align': 'right'
            },
            'Value': {
                'align': 'left'
            }
        }

    def __models_to_hash(self, models):
        return [model.to_dict() for model in models] if isinstance(models, list) else models.to_dict()

    def __models_to_json(self, models):
        return json.dumps(self.__models_to_hash(models))

    def __output_to_table(self, models, table_options):
        # column_options = self._OutputTable__column_options_from_models(models)
        # table_data = [[getattr(model, key) for key in column_options.keys()] for model in models]

        # if table_options.get('transpose'):
        #     print(tabulate.tabulate(table_data, headers='keys', tablefmt='grid').transpose())
        # else:
        #     print(tabulate.tabulate(table_data, headers='keys', tablefmt='grid', maxcolwidths=[table_options.get('width', self.terminal_width())]))

        # print(tabulate.tabulate(table_data, headers='keys', tablefmt='grid', maxcolwidths=[table_options.get('width', self._OutputTable__terminal_width())]))

        headers = models[0].keys()
        table_data = []
        for model in models:
            table_data.append(model.values())
        print(tabulate.tabulate(table_data, headers, tablefmt='fancy_grid'))

        print(f"{len(table_data)} rows")

    def __resolve_models(self, models):
        for model in models:
            for k, v in model.items():
                if isinstance(v, dict):
                    model[k] = json.dumps(v)
                elif isinstance(v, list):
                    model[k] = ', '.join([json.dumps(x) if hasattr(x, 'to_dict') else str(x) for x in v])

    def __terminal_width(self):
        try:
            return os.get_terminal_size().columns
        except OSError:
            return 155

# Example usage
if __name__ == "__main__":
    opts = {'json': False, 'external_call': False, 'suppress_output': False}
    output_table = OutputTable(opts)
    models = [{'Key': 'example_key', 'Value': 'example_value'}]
    output_table.print_models(models)
