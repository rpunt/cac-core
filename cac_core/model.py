import json
from collections.abc import Iterable

class Model:
    """
    A class to represent a generic data model.

    The Model class is designed to handle nested dictionaries and lists, converting them into
    instances of the Model class. It provides methods to add keys, convert to JSON, compare
    instances, and process nested models.

    Attributes:
        static_methods (set): A set of keys representing the attributes of the model.
        data (dict): A dictionary to store the data of the model.

    Methods:
        __init__(self, data, keys_to_remove=None):
            Initializes the Model instance with the given data and optional keys to remove.
        add_key(self, key, value):
            Adds a key to the model and creates getter and setter methods for it.
        __iter__(self):
            Iterates over the key-value pairs in the model.
        __str__(self):
            Returns a string representation of the model.
        to_json(self):
            Converts the model to a JSON string.
        __eq__(self, other):
            Compares the current model with another model.
        keys(self):
            Returns a list of keys in the model.
        to_dict(self):
            Converts the model to a dictionary.
        key_order(self):
            Returns the order of keys in the model.
        set_key_order(self, key_order):
            Sets the order of keys in the model.
        column_options(self):
            Returns the column options for the model.
        set_column_options(self, column_options):
            Sets the column options for the model.
        remove_keys(self):
            Returns the keys to be removed from the model.
        set_remove_keys(self, remove_keys):
            Sets the keys to be removed from the model.
        current_state(self):
            Returns the current state of the model as a string.
        _process_results(self, value):
            Processes the results of the model, converting nested models to dictionaries.
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
        setattr(self, key, self.data.get(key))
        setattr(self, f"{key}=", lambda val: self.data.update({key: val}))

    def __iter__(self):
        for key in self.static_methods:
            yield key, getattr(self, key)

    def __str__(self):
        return f"#<{self.__class__.__name__} {self.current_state()}>"

    def to_json(self):
        return json.dumps(self.to_dict())

    def __eq__(self, other):
        return self.current_state() == other.current_state()

    def keys(self):
        return list(self.static_methods)

    def to_dict(self):
        return {key: self._process_results(getattr(self, key)) for key in self.static_methods}

    def key_order(self):
        return getattr(self, '_key_order', self.keys())

    def set_key_order(self, key_order):
        self._key_order = key_order

    def column_options(self):
        return getattr(self, '_column_options', {})

    def set_column_options(self, column_options):
        if not isinstance(column_options, dict):
            raise ValueError('Column options needs to be a dictionary')
        self._column_options = column_options

    def remove_keys(self):
        return getattr(self, '_remove_keys', [])

    def set_remove_keys(self, remove_keys):
        self._remove_keys = list(remove_keys)

    def current_state(self):
        return ' '.join(f"{key}={getattr(self, key)}" for key in self.static_methods)

    def _process_results(self, value):
        if isinstance(value, Model):
            return value.to_dict()
        elif isinstance(value, list):
            return [self._process_results(val) for val in value]
        else:
            return value
