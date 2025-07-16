import time

class Heartbeat:
    def __init__(self, interval=10):
        self.interval = interval
        self.last_beat = time.time()
    def beat(self):
        self.last_beat = time.time()
    def is_alive(self):
        return (time.time() - self.last_beat) < (self.interval * 2)