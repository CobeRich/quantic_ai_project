from typing import List

# Lightweight policy-topic keywords.
# If none match, we refuse as "outside corpus" (basic assignment guardrail).
POLICY_KEYWORDS: List[str] = [
    "policy", "pto", "vacation", "leave", "holiday", "security", "password",
    "expense", "reimbursement", "remote", "work from home", "code of conduct",
    "benefits", "travel", "incident", "compliance", "hr", "employee"
]

def is_in_scope(question: str) -> bool:
    """Return True if question appears related to company policy corpus."""
    q = question.lower()
    return any(k in q for k in POLICY_KEYWORDS)

def trim_words(text: str, max_words: int = 180) -> str:
    """Limit output length to enforce concise answers."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " ..."
