python3 - <<'PY'
from dotenv import load_dotenv
load_dotenv()
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL"))
res = client.embeddings.create(
    model=os.getenv("EMBEDDING_MODEL"),
    input="test embedding"
)
print("OK, embedding length:", len(res.data[0].embedding))
PY
