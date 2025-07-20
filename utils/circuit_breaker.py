import time
import logging

class CircuitBreaker:
    def __init__(self, max_failures=3, reset_timeout=30):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure = 0
        self.open = False

    def call(self, func, *args, **kwargs):
        if self.open and (time.time() - self.last_failure < self.reset_timeout):
            logging.warning("Circuit breaker open. Skipping call.")
            raise Exception("Circuit breaker open.")
        try:
            result = func(*args, **kwargs)
            self.failures = 0
            self.open = False
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.max_failures:
                self.open = True
                logging.error("Circuit breaker tripped!")
            raise