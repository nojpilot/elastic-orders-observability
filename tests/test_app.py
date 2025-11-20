from service.app import app


def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_order_ok():
    client = app.test_client()
    response = client.post("/orders", json={"customer": "alice", "total": 10})
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "accepted"
    assert isinstance(body["id"], int)


def test_create_order_validation():
    client = app.test_client()
    response = client.post("/orders", json={"customer": "alice", "total": -1})
    assert response.status_code == 400
