# -*- coding: utf8 -*-



class Store(object):
    """
    分级存储
    """
    def __init__(self):
        self.store = dict()

    def get_keys(self):
        return self.store.keys()

    def get_content(self, key):
        try:
            return self.store[key]
        except:
            return None

    def add(self, key, value):
        self.store[key] = value



store = Store()
