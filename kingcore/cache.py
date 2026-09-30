"""Small bounded TTL cache. Local only; not a cross-process invalidation bus."""
from collections import OrderedDict
from copy import deepcopy
from threading import RLock
from time import monotonic

class TTLCache:
    def __init__(self, maxsize=500, ttl=60, clock=monotonic):
        if maxsize < 1 or ttl <= 0:
            raise ValueError("maxsize e ttl precisam ser positivos")
        self.maxsize, self.ttl, self.clock = maxsize, ttl, clock
        self._data = OrderedDict()
        self._lock = RLock()

    def _expire(self):
        now = self.clock()
        for key, (until, _) in list(self._data.items()):
            if until <= now:
                del self._data[key]

    def get(self, key, default=None):
        with self._lock:
            self._expire()
            item = self._data.get(key)
            if item is None:
                return default
            self._data.move_to_end(key)
            return deepcopy(item[1])

    def put(self, key, value):
        with self._lock:
            self._expire()
            self._data[key] = (self.clock() + self.ttl, deepcopy(value))
            self._data.move_to_end(key)
            while len(self._data) > self.maxsize:
                self._data.popitem(last=False)

    def invalidate(self, key=None):
        with self._lock:
            if key is None:
                self._data.clear()
            else:
                self._data.pop(key, None)
