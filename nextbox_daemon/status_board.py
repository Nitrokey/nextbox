from copy import deepcopy
from threading import RLock
from queue import Queue

class StatusBoard:
    def __init__(self):
        self.lock = RLock()
        self._board = {}
        self.messages = Queue()

    def contains_key(self, key):
        with self.lock:
            contains = key in self._board.keys()
        return contains

    def delete_key(self, key):
        with self.lock:
            if key in self._board.keys():
                del self._board[key]

    def get_keys(self):
        out = None
        with self.lock:
            out = list(self._board.keys())
        return out

    def get(self, key):
        out = None
        with self.lock:
            out = deepcopy(self._board.get(key))
        return out
    
    def set(self, key, val):
        with self.lock:
            self._board[key] = deepcopy(val)
        return True

    def update(self, key, dct):
        if not isinstance(dct, dict):
            self.messages.put(f"can't update key: {key}, dct: '{dct}'' is not a dict-type")
            return
        
        with self.lock:
            self._board.setdefault(key, {}).update(deepcopy(dct))

    def save(self):
        ...

    
board = StatusBoard()

    


    