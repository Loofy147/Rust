import redis
import os
import json

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
r = redis.Redis.from_url(REDIS_URL)
QUEUE_NAME = os.environ.get('REDIS_QUEUE', 'agentsys-tasks')

# Enqueue a task (as JSON)
def enqueue_task(task):
    r.rpush(QUEUE_NAME, json.dumps(task))

# Dequeue a task (blocking pop)
def dequeue_task(timeout=5):
    item = r.blpop(QUEUE_NAME, timeout=timeout)
    if item:
        _, data = item
        return json.loads(data)
    return None

# Get queue length
def queue_length():
    return r.llen(QUEUE_NAME)