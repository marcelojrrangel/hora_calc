class TestIndex:
    def test_get_index(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestRegisterMeeting:
    def test_register_success(self, client):
        response = client.post(
            "/registrar",
            data={"nome": "Daily", "inicio": "09:00", "fim": "09:15"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["meeting"] == "Daily"

    def test_register_invalid_time(self, client):
        response = client.post(
            "/registrar",
            data={"nome": "Invalid", "inicio": "10:00", "fim": "09:00"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "End time" in data["detail"]

    def test_register_missing_fields(self, client):
        response = client.post("/registrar", data={"nome": "Test"})
        assert response.status_code == 422


class TestGetMeetings:
    def test_get_meetings_empty(self, client):
        response = client.get("/reunioes")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_meetings_with_date(self, client):
        response = client.get("/reunioes?data=2026-07-19")
        assert response.status_code == 200

    def test_get_meetings_invalid_date(self, client):
        response = client.get("/reunioes?data=invalid")
        assert response.status_code == 400


class TestCalculator:
    def test_get_calculadora(self, client):
        response = client.get("/calculadora")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestLoginRateLimit:
    def test_failed_login_increments_attempt_counter(self, client):
        for i in range(5):
            response = client.post("/login", data={"password": "wrong"})
            assert response.status_code == 401

        # 6th attempt should be rate limited
        response = client.post("/login", data={"password": "wrong"})
        assert response.status_code == 429
        assert response.headers["Retry-After"].isdigit()
        assert int(response.headers["Retry-After"]) > 0

    def test_successful_login_resets_rate_limiter(self, client):
        for _ in range(4):
            client.post("/login", data={"password": "wrong"})

        response = client.post(
            "/login",
            data={"password": "test-password"},
            follow_redirects=False,
        )
        assert response.status_code == 302

        # After success, previous failed attempts should be cleared
        response = client.post("/login", data={"password": "wrong"})
        assert response.status_code == 401

    def test_rate_limit_is_per_ip(self, client):
        # Five failed attempts from one IP
        for _ in range(5):
            client.post("/login", data={"password": "wrong"})

        # Same request but from a different simulated IP should succeed
        response = client.post(
            "/login",
            data={"password": "wrong"},
            headers={"X-Forwarded-For": "10.0.0.1"},
        )
        assert response.status_code == 401


class TestSummary:
    def test_summary_empty(self, client):
        response = client.get("/resumo?data=2099-01-01")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["total"] == "0min"

    def test_remaining(self, client):
        response = client.get("/resumo/restante")
        assert response.status_code == 200
        data = response.json()
        assert "remaining_minutes" in data
        assert data["remaining_minutes"] >= 0
