"""
Replacement for shelve, using json.
This was needed to correctly support db between Python 2 and 3.
"""

__all__ = ["JsonStore"]

import io
from json import load, dump
from os.path import exists


class JsonStore:

    def __init__(self, filename):
        self.filename = filename
        self.data = {}
        if exists(filename):
            try:
                with io.open(filename, encoding='utf-8') as fd:
                    self.data = load(fd)
            except ValueError:
                print("Unable to read the state.db, content will be replaced.")

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        self.sync()

    def __delitem__(self, key):
        del self.data[key]
        self.sync()

    def __contains__(self, item):
        return item in self.data

    def get(self, item, default=None):
        return self.data.get(item, default)

    def keys(self):
        return self.data.keys()

    def sync(self):
        with open(self.filename, 'w') as fd:
            dump(self.data, fd, ensure_ascii=False)
