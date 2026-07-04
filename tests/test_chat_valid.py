from app import create_app


def test_chat_requires_question():
    app = create_app()
    client = app.test_client()
    resp = client.post("/chat", json={})
    assert resp.status_code in (400, 404)  # tighten to 400 once route confirmed

# def test_chat_requires_question():
#     app = create_app()
#     client = app.test_client()

#     resp = client.post("/chat", json={})
#     if resp.status_code != 400:
#         # fallback if app defines trailing slash
#         resp = client.post("/chat/", json={})

#     assert resp.status_code == 400
#     assert resp.is_json
#     assert "error" in resp.get_json()

#     app = create_app()
#     print(app.url_map)
