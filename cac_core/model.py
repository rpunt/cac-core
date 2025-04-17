# pylint: disable=line-too-long

"""
Model module for the Command and Control (CAC) Core package.

This module provides the Model class, which is the foundation for all data models
in the CAC framework. It implements dynamic attribute creation, dictionary-like
access methods, and handles nested data structures.

The Model class automatically converts nested dictionaries into Model instances
and supports serialization to dictionaries and JSON for data exchange.
"""

import json
# from collections.abc import Iterable

class Model:
    """
    Base class for all data models in the CAC framework.

    Model provides dynamic attribute creation and dictionary-like access to data,
    with support for nested models, serialization, and comparison operations.
    It automatically converts nested dictionaries into Model instances and offers
    methods for converting to dictionaries and JSON for data exchange.

    Attributes:
        data (dict): The underlying data dictionary.
        static_methods (set): Set of dynamically created attribute names.
    """

    def __init__(self, data, keys_to_remove=None):
        self.static_methods = set()
        self.data = {}

        if keys_to_remove is None:
            keys_to_remove = self.remove_keys()

        for key, value in data.items():
            if key in keys_to_remove:
                continue

            self.static_methods.add(key)
            self.add_key(key, value)

            if isinstance(value, list):
                self.data[key] = [Model(val, keys_to_remove) if isinstance(val, dict) else val for val in value]
            elif isinstance(value, dict):
                self.data[key] = Model(value, keys_to_remove)
            else:
                self.data[key] = value

    def add_key(self, key, value):
        """
        Adds a key to the model and creates getter and setter methods for it.

        This method dynamically adds an attribute to the model with the given key name,
        initializes it with the corresponding value from the data dictionary, and creates
        a setter method to update the value.

        Args:
            key (str): The key to add to the model.
            value: The value to associate with the key.
        """
        setattr(self, key, self.data.get(key))
        setattr(self, f"{key}=", lambda val: self.data.update({key: val}))

    def __iter__(self):
        for key in self.static_methods:
            yield key, getattr(self, key)

    def items(self):
        """
        Returns a view of the model's key-value pairs, similar to dict.items().

        Returns:
            list: A list of (key, value) tuples for all keys in the model.
        """
        result = []
        for key in self.static_methods:
            # Get the actual value from data dictionary instead of using getattr
            value = self.data.get(key)
            result.append((key, value))
        return result

    def values(self):
        """
        Returns the values of the model, similar to dict.values().

        Returns:
            list: A list of values for all keys in the model.
        """
        return [self.data.get(key) for key in self.static_methods]

    def __str__(self):
        return f"#<{self.__class__.__name__} {self.current_state()}>"

    def to_json(self):
        """
        Converts the model to a JSON string.

        Returns:
            str: A JSON string representation of the model.
        """
        return json.dumps(self.to_dict())

    def __eq__(self, other):
        return self.current_state() == other.current_state()

    def keys(self):
        """
        Returns a list of keys in the model.

        Returns:
            list: A list of all keys in the model.
        """
        return list(self.static_methods)

    def to_dict(self):
        """
        Converts the model to a dictionary.

        Returns:
            dict: A dictionary containing all key-value pairs from the model,
                  with nested models also converted to dictionaries.
        """
        return {key: self._process_results(self.data.get(key)) for key in self.static_methods}

    def remove_keys(self):
        """
        Returns the list of keys to be excluded from the model.

        Returns:
            list: A list of keys that should be removed when processing data.
        """
        return getattr(self, '_remove_keys', [])

    def set_remove_keys(self, remove_keys):
        """
        Sets the list of keys to be excluded from the model.

        Args:
            remove_keys (list): A list of keys to exclude when processing data.
        """
        self._remove_keys = list(remove_keys)

    def current_state(self):
        """
        Returns a string representation of the current state of the model.

        The string includes key-value pairs for all attributes in the model,
        formatted as "key=value key2=value2 ...".

        Returns:
            str: A string representation of the model's current state.
        """
        return ' '.join(f"{key}={getattr(self, key)}" for key in self.static_methods)

    def _process_results(self, value):
        if isinstance(value, Model):
            return value.to_dict()
        if isinstance(value, list):
            return [self._process_results(val) for val in value]
        return value
