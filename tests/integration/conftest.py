import hashlib

import pytest
from fastapi.testclient import TestClient

from app.auth import create_session
from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    salt = "test-salt"
    password = "test-password"
    password_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

    monkeypatch.setattr("app.config.settings.auth_password_hash", password_hash)
    monkeypatch.setattr("app.config.settings.auth_salt", salt)

    app = create_app()
    app.state.use_cases._repository._data_dir = tmp_path
    test_client = TestClient(app, raise_server_exceptions=False)

    token = create_session()
    test_client.cookies.set("session_token", token)

    return test_client
