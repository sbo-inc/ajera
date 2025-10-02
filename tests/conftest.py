import os

import pytest


# Ensure Ajera credentials are set for tests
@pytest.fixture(scope="session", autouse=True)
def ensure_ajera_credentials():
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test_key"
