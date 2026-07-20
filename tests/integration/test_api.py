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
