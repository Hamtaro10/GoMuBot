import pomice
from pomice import Queue

class GomuQueue(Queue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.history: list[pomice.Track] = []
        self.last_track: pomice.Track = None

    def qsize(self):
        return len(self._queue)
        