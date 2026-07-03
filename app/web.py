from flask import Blueprint, request, jsonify

web_bp = Blueprint("web", __name__)

@web_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@web_bp.get("/")
def home():
    # Minimal HTML chat page for requirement compliance
    return """
    <!doctype html>
    <html>
      <head><title>Policy RAG Assistant</title></head>
      <body>
        <h1>Policy RAG Assistant</h1>
        <form id="chat-form">
          <input id="q" type="text" placeholder="Ask a policy question" size="60"/>
          <button type="submit">Ask</button>
        </form>
        <pre id="out"></pre>
        <script>
          const form = document.getElementById('chat-form');
          const out = document.getElementById('out');
          form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const question = document.getElementById('q').value;
            const res = await fetch('/chat', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({question})
            });
            const data = await res.json();
            out.textContent = JSON.stringify(data, null, 2);
          });
        </script>
      </body>
    </html>
    """, 200

@web_bp.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()

    if not question:
        return jsonify({"error": "question is required"}), 400

    # Placeholder until RAG pipeline is wired in next steps
    return jsonify({
        "answer": "RAG pipeline not connected yet.",
        "citations": [],
        "snippets": [],
    }), 200
