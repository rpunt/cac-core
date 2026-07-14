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


class Output:
    """
    Handles the formatting and display of data in the CAC framework.

    This class provides functionality to output data as tables or JSON,
    with support for various formatting options and terminal width detection.
    It can also convert models to dictionaries for external API calls.

    Attributes:
        params (dict): Options that control output behavior
        logger (Logger): Logger instance for output messages
    """

    def __init__(self, params):
        self.opts = params
        self.logger = self.__create_logger()

    def print_models(self, data_models, table_options=None):
        """
        Display data models in the configured output format (table or JSON).

        This method formats and displays the provided models according to the
        output format specified in the params dictionary. It handles both
        individual models and collections of models.

        For JSON output:
        - Models are converted to dictionaries and output as JSON strings
        - Nested structures are preserved in their original form

        For table output:
        - Complex nested structures are flattened for tabular display
        - Headers are the union of all models' keys (first-seen order)
        - Displays a row count after the table

        Args:
            data_models (Model or list): One or more models to display. Can be a single
                Model instance or a list of Model instances.
            table_options (dict, optional): Options for configuring table output:
                - headers: Custom header mappings (dict)
                - exclude: List of columns to exclude
                - formatters: Dict mapping column names to formatter functions
                - width: Dict mapping column names to fixed widths

        Returns:
            None: Output is printed directly to stdout

        Usage:
            # Basic usage with table output (default)
            output = Output({"output": "table"})
            output.print_models(models)

            # JSON output
            output = Output({"output": "json"})
            output.print_models(models)

            # Customized table with formatting options
            output = Output({"output": "table"})
            options = {
                "headers": {"id": "ID", "name": "Full Name"},
                "exclude": ["internal_id", "metadata"]
            }
            output.print_models(models, options)

            # Handle single model case
            output.print_models(single_model)

        Note:
            If no models are provided for table output, a "No results were found"
            message will be logged and nothing will be displayed.
        """
        if table_options is None:
            table_options = {}

        output_format = self._get_param("output", "table")
        if output_format == "json":
            self.__output_to_json(data_models)
            return

        if output_format == "table":
            # For table output, resolve models (flatten complex structures)
            data_models = (
                list(data_models) if isinstance(data_models, list) else [data_models]
            )
            if not data_models:
                self.logger.info("No results were found")
                return
            resolved = self.__resolve_models(data_models)
            self.__output_to_table(resolved, table_options)

    def _get_param(self, key, default=None):
        """
        Safely get a parameter value from self.opts, handling both dict and Namespace types.

        Args:
            key (str): Parameter key to look up
            default: Default value if key not found

        Returns:
            Value of the parameter or default
        """
        if self.opts is None:
            return default

        # Handle Namespace objects
        if hasattr(self.opts, "__dict__"):
            return getattr(self.opts, key, default)

        # Handle dictionary objects
        elif isinstance(self.opts, dict):
            return self.opts.get(key, default)

        # Fallback
        return default

    def __create_logger(self):
        logger = logging.getLogger("OutputTable")
        logger.setLevel(logging.INFO)
        # The named logger is a process-wide singleton; only attach a handler
        # once so repeated Output() instances don't produce duplicate output.
        if not logger.handlers:
            sh = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] (%(processName)s %(threadName)s) %(module)s:%(lineno)d: %(message)s"
            )
            sh.setFormatter(formatter)
            logger.addHandler(sh)
            # Don't also bubble to ancestor handlers (e.g. root) and double-log.
            logger.propagate = False
        return logger

    def __models_to_dict(self, data_models):
        return (
            [model.to_dict() for model in data_models]
            if isinstance(data_models, list)
            else data_models.to_dict()
        )

    def __output_to_json(self, data_models):
        print(json.dumps(self.__models_to_dict(data_models)))

    def __output_to_table(self, data_models, table_options=None):
        if not data_models:
            return

        table_options = table_options or {}
        exclude = set(table_options.get("exclude") or [])
        header_map = table_options.get("headers") or {}
        formatters = table_options.get("formatters") or {}
        widths = table_options.get("width") or {}

        # Union of column keys across all rows (first-seen order), so columns
        # present only in later rows are not silently dropped.
        columns = []
        for model in data_models:
            for key in model.keys():
                if key not in exclude and key not in columns:
                    columns.append(key)

        # Display headers honor any custom header mappings
        headers = [header_map.get(key, key) for key in columns]

        table_data = []
        for model in data_models:
            row = []
            for key in columns:
                value = model.get(key)
                if key in formatters:
                    value = formatters[key](value)
                row.append(value)
            table_data.append(row)

        # Per-column fixed widths, aligned with the column order (None = auto)
        maxcolwidths = (
            [widths.get(key) for key in columns]
            if any(key in widths for key in columns)
            else None
        )

        print(
            tabulate.tabulate(
                table_data,
                headers,
                tablefmt="pretty",
                stralign="left",
                numalign="right",
                maxcolwidths=maxcolwidths,
            )
        )
        row_count = len(table_data)
        print(f"{row_count} {'row' if row_count == 1 else 'rows'}")

    def __resolve_models(self, data_models):
        # Build flattened plain-dict rows WITHOUT mutating the caller's models;
        # rendering must not corrupt the caller's data as a side effect.
        resolved = []
        for model in data_models:
            row = {}
            for k, v in model.items():
                if isinstance(v, list):
                    row[k] = ", ".join(
                        [
                            (
                                json.dumps(x.to_dict())
                                if hasattr(x, "to_dict")
                                else (json.dumps(x) if isinstance(x, dict) else str(x))
                            )
                            for x in v
                        ]
                    )
                elif hasattr(v, "to_dict"):
                    row[k] = json.dumps(v.to_dict())
                elif isinstance(v, dict):
                    row[k] = json.dumps(v)
                else:
                    row[k] = v
            resolved.append(row)
        return resolved


# Example usage
if __name__ == "__main__":
    opts = {"json": False, "external_call": False, "suppress_output": False}
    output_table = Output(opts)
    models = [{"Key": "example_key", "Value": "example_value"}]
    output_table.print_models(models)
