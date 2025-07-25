import asyncio
import pytest
from unittest.mock import Mock, patch
from app.orchestrator.retry import retry_with_exponential_backoff

@pytest.mark.asyncio
async def test_retry_mechanism():
    mock_task = Mock()
    mock_task.side_effect = [Exception("Task failed"), Exception("Task failed"), 42]

    @retry_with_exponential_backoff(retries=3, backoff_in_seconds=0.1)
    async def task_to_retry():
        return mock_task()

    result = await task_to_retry()
    assert result == 42
    assert mock_task.call_count == 3
