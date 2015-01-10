"""
A module containing various useful data structures.
"""


class DictionaryForUnhashables():
    """
    A dictionary-like data structure that is capable of storing unhashable items.
    """

    def __init__(self):
        self.keys = {}
        self.values = []
        self.empty_indices = set()


    def add(self, key, value):
        """
        A method to add key-value pairs to the data structure.
        """
        if key in self.keys:
            raise Exception('Key -- %s -- already used.' % key)
        if len(self.empty_indices) == 0:
            self.keys[key] = len(self.values)
            self.values.append(value)
        else:
            index = self.empty_indices.pop()
            self.keys[key] = index
            self.values[index] = value


    def remove(self, key):
        """
        A method to remove key-value pairs from the data structure.
        """
        index = self.keys[key]
        self.empty_indices.add(index)
        del self.keys[key]
        self.values[index] = 'empty'


    def contains(self, key):
        """
        A method to check if a key exists in the data structure.
        """
        return key in self.keys


    def get(self, key):
        """
        A method to return a value from the data structure given its key.
        """
        if self.contains(key):
            index = self.keys[key]
            return self.values[index]
        else:
            raise Exception('Item -- %s -- not in data structure.' % key)
