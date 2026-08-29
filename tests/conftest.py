import os
import pytest
import asyncio
from orchestrator.config import settings

# Force MOCK_MODE for automated testing
os.environ["MOCK_MODE"] = "true"
settings.MOCK_MODE = True

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
