import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from main import app, get_db
from db import Base

# A separate, throwaway database just for tests.
TEST_ENGINE = create_engine("sqlite:///./test.db")


@pytest.fixture()
def client():
    # Fresh tables before each test
    Base.metadata.create_all(TEST_ENGINE)

    def override_get_db():
        db = Session(TEST_ENGINE)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    # Clean up after each test so tests don't affect each other
    app.dependency_overrides.clear()
    Base.metadata.drop_all(TEST_ENGINE)