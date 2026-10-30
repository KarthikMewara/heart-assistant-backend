import os
os.environ["DATABASE_URL"] = "sqlite:///./storage/test.db"   # must be set before importing the app

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post("/auth/register", json={"email": "asha@example.com", "password": "secret123",
                                        "name": "Asha", "age": 70, "sex": "F"})
    token = client.post("/auth/login", data={"username": "asha@example.com",
                                             "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}