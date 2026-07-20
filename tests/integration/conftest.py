import bcrypt
import pytest
from fastapi.testclient import TestClient

from app.auth import create_session
from app.main import create_app
from app.rate_limiter import login_rate_limiter


@pytest.fixture(autouse=True)
def clear_login_rate_limiter():
    login_rate_limiter.reset_all()
    yield
    login_rate_limiter.reset_all()


@pytest.fixture
def client(tmp_path, monkeypatch):
    password = "test-password"
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(4)).decode()

    monkeypatch.setattr("app.config.settings.auth_password_hash", password_hash)

    app = create_app()
    app.state.use_cases._repository._data_dir = tmp_path
    test_client = TestClient(app, raise_server_exceptions=False)

    token = create_session()
    test_client.cookies.set("session_token", token)

    return test_client
