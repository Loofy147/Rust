import time
import logging
from functools import wraps

def retry(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        retries = 3
        delay = 2
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.warning(f"Retry {attempt+1}/{retries} after error: {e}")
                time.sleep(delay * (2 ** attempt))
        raise Exception(f"Failed after {retries} retries.")
    return wrapper