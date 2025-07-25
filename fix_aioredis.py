import os

file_path = "/home/jules/.pyenv/versions/3.12.11/lib/python3.12/site-packages/aioredis/exceptions.py"

with open(file_path, "r") as f:
    content = f.read()

content = content.replace(
    "class TimeoutError(asyncio.TimeoutError, builtins.TimeoutError, RedisError):",
    "class TimeoutError(asyncio.TimeoutError, RedisError):"
)

with open(file_path, "w") as f:
    f.write(content)
