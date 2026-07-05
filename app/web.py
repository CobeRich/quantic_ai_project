import os
from flask import Blueprint, current_app, request, jsonify
from .guardrails import is_in_scope, trim_words

web_bp = Blueprint("web", __name__)

@web_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@web_bp.get("/")
def home():
    author = os.getenv("PROJECT_AUTHOR", "R. Owusu")
    return """
    <!doctype html>
    <html lang="en">
      <head><title>Policy RAG Assistant</title></head>
      <body>
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Space+Grotesk:wght@400;500;700&display=swap');

          :root {
            --bg-1: #061a1f;
            --bg-2: #12343b;
            --paper: #f7f4ec;
            --ink: #112026;
            --brand: #15b097;
            --brand-2: #ff8f3f;
            --muted: #4b6570;
          }

          * { box-sizing: border-box; }

          body {
            margin: 0;
            min-height: 100vh;
            font-family: 'Space Grotesk', sans-serif;
            color: var(--ink);
            background:
              radial-gradient(circle at 20% 10%, rgba(21,176,151,0.18), transparent 35%),
              radial-gradient(circle at 80% 90%, rgba(255,143,63,0.2), transparent 40%),
              linear-gradient(140deg, var(--bg-1), var(--bg-2));
            display: grid;
            place-items: center;
            padding: 24px;
          }

          .shell {
            width: min(920px, 100%);
            background: var(--paper);
            border-radius: 22px;
            padding: 28px;
            box-shadow: 0 24px 60px rgba(0,0,0,0.35);
            animation: rise 500ms ease-out;
          }

          .title {
            margin: 0;
            font-family: 'Fraunces', serif;
            font-size: clamp(1.8rem, 4vw, 2.6rem);
            line-height: 1.05;
          }

          .subtitle {
            margin: 10px 0 22px;
            color: var(--muted);
          }

          .brand-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 12px;
          }

          .tag {
            background: linear-gradient(90deg, var(--brand), var(--brand-2));
            color: #042429;
            font-weight: 700;
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 0.85rem;
          }

          form {
            display: grid;
            gap: 12px;
          }

          label {
            font-weight: 700;
            font-size: 0.95rem;
          }

          input, textarea {
            width: 100%;
            border: 1.5px solid #c9d9dd;
            border-radius: 12px;
            padding: 12px 14px;
            font: inherit;
            color: var(--ink);
            background: #ffffff;
          }

          input:focus, textarea:focus {
            outline: 3px solid rgba(21,176,151,0.22);
            border-color: var(--brand);
          }

          textarea {
            min-height: 170px;
            resize: vertical;
          }

          .actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
          }

          button {
            border: 0;
            border-radius: 12px;
            padding: 11px 16px;
            font: inherit;
            font-weight: 700;
            cursor: pointer;
          }

          #ask {
            background: #0d7f71;
            color: #ffffff;
          }

          #clear {
            background: #e6edf0;
            color: #18313a;
          }

          .meta {
            margin-top: 16px;
            color: #2d4a55;
            font-size: 0.9rem;
          }

          @keyframes rise {
            from { transform: translateY(10px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
          }
        </style>

        <main class="shell">
          <div class="brand-row">
            <p class="tag">Quantic Project Assistant</p>
            <p class="meta">Author: """ + author + """</p>
          </div>

          <h1 class="title">Ask Company Policy Questions</h1>
          <p class="subtitle">Type your query and receive grounded policy feedback in the response box.</p>

          <form id="chat-form">
            <label for="q">Your Query</label>
            <input id="q" type="text" placeholder="Example: What is the PTO carryover policy?" />

            <div class="actions">
              <button id="ask" type="submit">Get Feedback</button>
              <button id="clear" type="button">Clear</button>
            </div>

            <label for="answer">Response</label>
            <textarea id="answer" readonly placeholder="Response will appear here..."></textarea>

            <label for="sources">Citations</label>
            <textarea id="sources" readonly placeholder="Citations will appear here..."></textarea>
          </form>
        </main>

        <script>
          const form = document.getElementById('chat-form');
          const input = document.getElementById('q');
          const answer = document.getElementById('answer');
          const sources = document.getElementById('sources');
          const clearButton = document.getElementById('clear');

          clearButton.addEventListener('click', () => {
            input.value = '';
            answer.value = '';
            sources.value = '';
            input.focus();
          });

          form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const question = input.value.trim();

            if (!question) {
              answer.value = 'Please type a query first.';
              sources.value = '';
              return;
            }

            answer.value = 'Loading response...';
            sources.value = '';

            try {
              const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question})
              });

              const raw = await res.text();
              let data = {};
              try {
                data = raw ? JSON.parse(raw) : {};
              } catch {
                data = {answer: raw || 'Unexpected server response', citations: []};
              }

              if (!res.ok) {
                answer.value = data.error || data.answer || ('Request failed with status ' + res.status + '.');
                sources.value = '';
                return;
              }

              answer.value = data.answer || 'No answer returned.';
              const citationLines = (data.citations || []).map((c) => {
                return (c.doc_title || 'unknown') + ' :: ' + (c.chunk_id || 'unknown');
              });
              sources.value = citationLines.length ? citationLines.join(' | ') : 'No citations returned.';
            } catch (err) {
              answer.value = 'Request failed. Please try again.';
              sources.value = String(err);
            }
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

    if not is_in_scope(question):
        return jsonify({
            "answer": "I can only answer questions about company policies and procedures in this corpus.",
            "citations": [],
            "snippets": [],
        }), 200

    k = int(os.getenv("TOP_K", "4"))
    try:
        from .rag import answer_with_rag
        result = answer_with_rag(question, k=k)
        result["answer"] = trim_words(result.get("answer", ""), max_words=180)
        result.setdefault("citations", [])
        result.setdefault("snippets", [])
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.exception("chat failed")
        return jsonify({
            "answer": "Temporary backend issue. Please try again.",
            "error": str(e),
            "citations": [],
            "snippets": [],
        }), 200
