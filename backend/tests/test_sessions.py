def test_create_and_get_session(client):
    r = client.post("/sessions", json={"user_label": "test-user"})
    assert r.status_code == 200
    session = r.json()
    assert session["user_label"] == "test-user"

    r2 = client.get(f"/sessions/{session['id']}")
    assert r2.status_code == 200
    assert r2.json()["id"] == session["id"]


def test_get_nonexistent_session_404(client):
    r = client.get("/sessions/does-not-exist")
    assert r.status_code == 404
