import time


class SimpleTTLCache:
    def __init__(self, ttl_seconds=3600):
        self.ttl = ttl_seconds
        self._store = {}

    def get(self, key):
        entry = self._store.get(key)
        if not entry:
            return None

        value, ts = entry
        if time.time() - ts > self.ttl:
            del self._store[key]
            return None

        return value

    def set(self, key, value):
        self._store[key] = (value, time.time())
