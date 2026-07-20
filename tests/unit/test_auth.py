from datetime import datetime, timedelta

import bcrypt
import pytest

from app.auth import (
    _sessions,
    cleanup_expired_sessions,
    create_session,
    destroy_session,
    validate_session,
    verify_password,
)


@pytest.fixture(autouse=True)
def clear_sessions():
    _sessions.clear()
    yield
    _sessions.clear()


class TestVerifyPassword:
    def test_correct_password_bcrypt(self, monkeypatch):
        h = bcrypt.hashpw(b"secret", bcrypt.gensalt(10)).decode()
        monkeypatch.setattr("app.config.settings.auth_password_hash", h)
        assert verify_password("secret") is True

    def test_wrong_password_bcrypt(self, monkeypatch):
        h = bcrypt.hashpw(b"secret", bcrypt.gensalt(10)).decode()
        monkeypatch.setattr("app.config.settings.auth_password_hash", h)
        assert verify_password("wrong") is False

    def test_empty_hash_returns_false(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.auth_password_hash", "")
        assert verify_password("anything") is False

    def test_malformed_hash_returns_false(self, monkeypatch):
        monkeypatch.setattr(
            "app.config.settings.auth_password_hash", "$2b$not-a-valid-hash"
        )
        assert verify_password("anything") is False

    def test_non_bcrypt_hash_returns_false(self, monkeypatch):
        monkeypatch.setattr(
            "app.config.settings.auth_password_hash",
            "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
        )
        assert verify_password("password") is False


class TestSessions:
    def test_create_session_returns_token(self):
        token = create_session()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_validate_session_valid(self):
        token = create_session()
        assert validate_session(token) is True

    def test_validate_session_invalid(self):
        assert validate_session("nonexistent") is False

    def test_validate_session_expired(self):
        token = create_session()
        _sessions[token] = datetime.now() - timedelta(hours=1)
        assert validate_session(token) is False
        assert token not in _sessions

    def test_destroy_session(self):
        token = create_session()
        assert validate_session(token) is True
        destroy_session(token)
        assert validate_session(token) is False

    def test_destroy_nonexistent_session(self):
        destroy_session("nonexistent")

    def test_cleanup_expired_sessions(self):
        valid = create_session()
        expired = create_session()
        _sessions[expired] = datetime.now() - timedelta(hours=1)
        cleanup_expired_sessions()
        assert valid in _sessions
        assert expired not in _sessions
