import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    # Using the context manager form ensures FastAPI's startup event runs
    # (which creates tables), matching real server behavior.
    with TestClient(app) as c:
        yield c
