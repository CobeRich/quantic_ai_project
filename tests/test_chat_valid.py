from app import create_app


def test_chat_requires_question():
    app = create_app()
    client = app.test_client()
    resp = client.post("/chat", json={})
    assert resp.status_code == 400

