from threading import RLock

class StatusBoard:
    def __init__(self):
        self.lock = RLock()
        self._board = {}

    def get(self, key):
        out = None
        with self.lock:
            out = self._board.get(key)
        return out
    
    def set(self, key, val):
        with self.lock:
            self._board[key] = val
        return True

    def save(self):
        ...

    


    


    