# pylint: disable=line-too-long

"""
Model module for the CAC Core package.

This module provides the Model class, which is the foundation for all data models
in the CAC framework. It implements dynamic attribute creation, dictionary-like
access methods, and handles nested data structures.

The Model class automatically converts nested dictionaries into Model instances
and supports serialization to dictionaries and JSON for data exchange.
"""

import json
import copy
from typing import Any, Dict, List, Optional, Set, Tuple #, Union

class Model:
    """
    Base class for all data models in the CAC framework.

    Model provides dynamic attribute creation and dictionary-like access to data,
    with support for nested models, serialization, and comparison operations.
    It automatically converts nested dictionaries into Model instances and offers
    methods for converting to dictionaries and JSON for data exchange.

    Attributes:
        data (dict): The underlying data dictionary.
        field_names (set): Set of dynamically created attribute names.
    """

    def __init__(self, row_data: Dict[str, Any], keys_to_remove: Optional[List[str]] = None) -> None:
        self.field_names: Set[str] = set()
        self.data: Dict[str, Any] = {}
        self._key_order: List[str] = []
        self._formatters: Dict[str, Any] = {}
        self._remove_keys: List[str] = []

        if keys_to_remove is None:
            keys_to_remove = self.remove_keys()

        for key, value in row_data.items():
            if key in keys_to_remove:
                continue

            self.field_names.add(key)
            self._key_order.append(key)  # Track insertion order
            # Dynamically create getter and setter methods for each key
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
        # Create property for more Pythonic attribute access
        def getter(self, key=key):
            return self.data.get(key)

        def setter(self, value, key=key):
            self.data[key] = value

        prop = property(lambda self: getter(self), lambda self, val: setter(self, val))
        setattr(self.__class__, key, prop)

        # Keep existing methods for backward compatibility
        setattr(self, f"{key}=", lambda val, key=key: self.data.update({key: val}))

    def __iter__(self):
        for key in self.field_names:
            yield key, getattr(self, key)

    def items(self) -> List[Tuple[str, Any]]:
        """Returns key-value pairs as a list of tuples"""
        result = []
        for key in self.field_names:
            # Get the actual value from data dictionary instead of using getattr
            value = self.data.get(key)
            result.append((key, value))
        return result

    def values(self) -> List[Any]:
        """Returns values as a list"""
        return [self.data.get(key) for key in self.field_names]

    def __str__(self):
        return f"#<{self.__class__.__name__} {self.current_state()}>"

    def to_json(self):
        """
        Converts the model to a JSON string.

        Returns:
            str: A JSON string representation of the model.
        """
        return json.dumps(self.to_dict())

    # def __eq__(self, other):
    #     return self.current_state() == other.current_state()

    def keys(self):
        """
        Returns a list of keys in the model in their original insertion order.

        Returns:
            list: A list of all keys in the model in insertion order.
        """
        return self._key_order

    def to_dict(self):
        """
        Converts the model to a dictionary.

        Returns:
            dict: A dictionary containing all key-value pairs from the model,
                  with nested models also converted to dictionaries.
        """
        # More efficient implementation using comprehension
        return {key: self._process_results(self.data.get(key)) for key in self._key_order}

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
        return ' '.join(f"{key}={getattr(self, key)}" for key in self.field_names)

    def _process_results(self, value):
        if isinstance(value, Model):
            return value.to_dict()
        if isinstance(value, list):
            return [self._process_results(val) for val in value]
        return value

    def get(self, key, default=None):
        """
        Returns the value for the given key, or the default if the key is not found.

        This method enables dictionary-like access to the model's attributes.

        Args:
            key (str): The key to look up.
            default: The value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value.
        """
        if key in self.field_names:
            return self.data.get(key)
        return default

    def __getitem__(self, key):
        """Dictionary-style access with model[key]"""
        if key in self.field_names:
            return self.data.get(key)
        raise KeyError(key)

    def __setitem__(self, key, value):
        """Dictionary-style assignment with model[key] = value"""
        if key not in self.field_names:
            self.field_names.add(key)
            self._key_order.append(key)
            self.add_key(key, value)
        self.data[key] = value

    def __contains__(self, key):
        """Support for 'in' operator: key in model"""
        return key in self.field_names

    def __len__(self):
        """Support for len(model)"""
        return len(self.field_names)

    def __repr__(self) -> str:
        """Developer-friendly string representation"""
        class_name = self.__class__.__name__
        attrs = ", ".join(f"{k}={repr(v)}" for k, v in list(self.items())[:3])
        if len(self.field_names) > 3:
            attrs += ", ..."
        return f"{class_name}({attrs})"

    def __copy__(self):
        """Support for copy.copy(model)"""
        new_model = self.__class__({}, [])
        new_model.data = copy.copy(self.data)
        new_model.field_names = copy.copy(self.field_names)
        new_model._key_order = copy.copy(self._key_order)
        return new_model

    def __deepcopy__(self, memo):
        """Support for copy.deepcopy(model)"""
        new_model = self.__class__({}, [])
        memo[id(self)] = new_model
        new_model.data = copy.deepcopy(self.data, memo)
        new_model.field_names = copy.deepcopy(self.field_names, memo)
        new_model._key_order = copy.deepcopy(self._key_order, memo)
        return new_model

    def validate(self) -> List[str]:
        """
        Validates the model against defined constraints.

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []
        # Child classes can implement specific validation logic
        return errors

    def is_valid(self) -> bool:
        """
        Returns True if the model passes all validation.

        Returns:
            bool: True if valid, False otherwise
        """
        return len(self.validate()) == 0

    # In Model class:

    def format_column(self, key, formatter):
        """Sets a formatter function for a specific column"""
        self._formatters[key] = formatter
        self._formatters[key] = formatter
