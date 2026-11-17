"""Pytest configuration and test session fixtures."""

import os
from pathlib import Path
import pytest
from app.core.config import settings
from app.db.session import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initializes SQLite database tables and temporary directories before tests run."""
    settings.TEMP_DIRECTORY.mkdir(parents=True, exist_ok=True)
    init_db()
    yield
