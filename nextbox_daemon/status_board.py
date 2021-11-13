from copy import deepcopy
from threading import RLock
from queue import Queue
from datetime import datetime as dt

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
        if not isinstance(val, dict):
            log.error(f"StatusBoard only accepts dicts as values - provided {type(val)}")
            return False

        with self.lock:
            self._board[key] = deepcopy(val)
            self._board[key]["when"] = dt.now().isoformat()

        return True

    def is_older_than(self, key, secs):
        if not self.contains_key(key):
            return True

        with self.lock:
            last = self.get(key).get("when")
            if not last: 
                return True
            secs_old = (dt.now() - dt.fromisoformat(last)).total_seconds()
        return secs_old > secs

    def save(self):
        ...

    
board = StatusBoard()

    


    