# -*- coding: utf8 -*-

import redis

class UnsupportException(Exception):
    pass


class Store(object):
    """
    分级存储
    """
    def __init__(self):
        pass

    def get_keys(self):
        raise UnsupportException

    def get_content(self, key):
        raise UnsupportException

    def add(self, key, value):
        raise UnsupportException


class MapStore(Store):
    def __init__(self):
        super(MapStore, self).__init__()
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


class RedisStore(Store):
    def __init__(self):
        super(RedisStore, self).__init__()
        self.redis_cli = redis.StrictRedis(host='localhost', port=6379, db=0, password="foobared")

    def get_keys(self):
        return self.redis_cli.keys()

    def get_content(self, key):
        return self.redis_cli.get(key)

    def add(self, key, value):
        self.redis_cli.set(key, value=value)


store = RedisStore()
