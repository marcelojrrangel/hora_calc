import hashlib
from datetime import datetime, timedelta

import pytest

from app.auth import (
    _hash_password,
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


class TestHashPassword:
    def test_hash_is_deterministic(self):
        assert _hash_password("test", "salt") == _hash_password("test", "salt")

    def test_different_passwords_different_hashes(self):
        assert _hash_password("a", "salt") != _hash_password("b", "salt")

    def test_different_salts_different_hashes(self):
        assert _hash_password("test", "salt1") != _hash_password("test", "salt2")


class TestVerifyPassword:
    def test_correct_password(self, monkeypatch):
        salt = "my-salt"
        hashed = hashlib.sha256(f"{salt}secret".encode()).hexdigest()
        monkeypatch.setattr("app.config.settings.auth_password_hash", hashed)
        monkeypatch.setattr("app.config.settings.auth_salt", salt)
        assert verify_password("secret") is True

    def test_wrong_password(self, monkeypatch):
        salt = "my-salt"
        hashed = hashlib.sha256(f"{salt}secret".encode()).hexdigest()
        monkeypatch.setattr("app.config.settings.auth_password_hash", hashed)
        monkeypatch.setattr("app.config.settings.auth_salt", salt)
        assert verify_password("wrong") is False

    def test_empty_hash_returns_false(self, monkeypatch):
        monkeypatch.setattr("app.config.settings.auth_password_hash", "")
        assert verify_password("anything") is False


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
