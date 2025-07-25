import asyncio
import random
from functools import wraps

def retry_with_exponential_backoff(retries=3, backoff_in_seconds=1):
    def rwb(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            _retries, _backoff = retries, backoff_in_seconds
            while _retries > 1:
                try:
                    return await f(*args, **kwargs)
                except Exception as e:
                    print(f"Task failed with error: {e}. Retrying in {_backoff} seconds...")
                    await asyncio.sleep(_backoff)
                    _retries -= 1
                    _backoff *= 2
            return await f(*args, **kwargs)
        return wrapper
    return rwb
