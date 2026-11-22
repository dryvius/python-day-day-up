from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_API_KEY = "test-api-key"
TEST_DATABASE_PATH = PROJECT_ROOT / ".pytest-todo.db"
os.environ["APP_API_KEY"] = TEST_API_KEY
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"

from todo_api.database import get_db
from todo_api.main import app
from todo_api.models import Todo


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Generator[None, None, None]:
    TEST_DATABASE_PATH.unlink(missing_ok=True)
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.attributes["configure_logger"] = False
    command.upgrade(alembic_config, "head")
    yield
    TEST_DATABASE_PATH.unlink(missing_ok=True)


@pytest.fixture
def client(migrated_database: None) -> Generator[TestClient, None, None]:
    engine = create_engine(
        f"sqlite:///{TEST_DATABASE_PATH}",
        connect_args={"check_same_thread": False},
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    with testing_session() as session:
        session.execute(delete(Todo))
        session.commit()
    app.dependency_overrides.clear()
    engine.dispose()
