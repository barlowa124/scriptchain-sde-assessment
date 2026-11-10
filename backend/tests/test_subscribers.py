from fastapi.testclient import TestClient

from app.main import create_app


def make_client(tmp_path):
    sent = []

    def fake_mailer(to_address, name):
        sent.append((to_address, name))

    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        mailer=fake_mailer,
    )
    return TestClient(app), sent


def test_health(tmp_path):
    client, _ = make_client(tmp_path)
    assert client.get("/api/health").json() == {"status": "ok"}


def test_create_subscriber_stores_row_and_sends_confirmation(tmp_path):
    client, sent = make_client(tmp_path)
    resp = client.post(
        "/api/subscribers",
        json={"name": "Ada Lovelace", "email": "Ada@Example.com"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Ada Lovelace"
    assert body["email"] == "ada@example.com"
    assert sent == [("ada@example.com", "Ada Lovelace")]


def test_duplicate_email_is_rejected(tmp_path):
    client, sent = make_client(tmp_path)
    payload = {"name": "Ada", "email": "ada@example.com"}
    assert client.post("/api/subscribers", json=payload).status_code == 201
    resp = client.post("/api/subscribers", json=payload)
    assert resp.status_code == 409
    assert len(sent) == 1


def test_invalid_email_is_rejected(tmp_path):
    client, sent = make_client(tmp_path)
    resp = client.post(
        "/api/subscribers", json={"name": "Ada", "email": "not-an-email"}
    )
    assert resp.status_code == 422
    assert sent == []


def test_blank_name_is_rejected(tmp_path):
    client, sent = make_client(tmp_path)
    resp = client.post(
        "/api/subscribers", json={"name": "", "email": "ada@example.com"}
    )
    assert resp.status_code == 422
    assert sent == []
