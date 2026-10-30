from app.services import llm


def _ollama_off(*args, **kwargs):
    raise llm.httpx.ConnectError("Ollama is off in tests")


def test_full_flow(client, auth_headers, monkeypatch):
    monkeypatch.setattr(llm.httpx, "post", _ollama_off)
    report = client.post("/reports/manual", headers=auth_headers,
                         json={"systolic_bp": 160, "total_cholesterol": 260, "fasting_glucose": 130}).json()
    analysis = client.post(f"/analysis/report/{report['id']}", headers=auth_headers).json()
    assert analysis["risk_level"] in {"low", "moderate", "high"}
    assert analysis["flags"][0]["status"] in {"high", "critical"}
    planned = client.post(f"/analysis/{analysis['id']}/plan", headers=auth_headers).json()
    assert planned["plan"]["source"] == "fallback"


def test_other_users_cannot_see_reports(client, auth_headers):
    report = client.post("/reports/manual", headers=auth_headers, json={"hdl": 50}).json()
    client.post("/auth/register", json={"email": "ravi@example.com", "password": "secret123", "name": "Ravi"})
    token = client.post("/auth/login", data={"username": "ravi@example.com", "password": "secret123"}).json()["access_token"]
    response = client.get(f"/reports/{report['id']}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_requires_login(client):
    assert client.get("/reports").status_code == 401


def test_emergency_check(client, auth_headers):
    result = client.post("/emergency/check", headers=auth_headers, json={"text": "I have chest pain"}).json()
    assert result["is_emergency"] is True