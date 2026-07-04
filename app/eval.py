import csv
import os
import time
import statistics
from typing import Dict, List, Any

from dotenv import load_dotenv
from app.rag import answer_with_rag

load_dotenv(".env")

EVAL_PATH = "data/eval/questions.csv"
OUT_PATH = "data/eval/results.csv"


def has_citations(resp: Dict[str, Any]) -> bool:
    """Simple citation presence check."""
    c = resp.get("citations", [])
    return isinstance(c, list) and len(c) > 0


def groundedness_heuristic(resp: Dict[str, Any]) -> int:
    """
    Heuristic groundedness proxy:
    returns 1 if answer exists and snippets exist; else 0.
    (You will still do manual spot-check for final writeup quality.)
    """
    answer = (resp.get("answer") or "").strip()
    snippets = resp.get("snippets", [])
    return int(bool(answer) and isinstance(snippets, list) and len(snippets) > 0)


def exact_partial_match(answer: str, gold: str) -> Dict[str, int]:
    """
    Optional EM/PM heuristic:
    - exact_match: normalized exact string match
    - partial_match: gold substring appears in answer (or vice versa)
    """
    a = " ".join((answer or "").lower().split())
    g = " ".join((gold or "").lower().split())
    exact = int(a == g and g != "")
    partial = int((g in a or a in g) and g != "" and a != "")
    return {"exact_match": exact, "partial_match": partial}


def percentile(values: List[float], p: float) -> float:
    """Compute percentile with simple interpolation."""
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return values_sorted[f]
    return values_sorted[f] + (values_sorted[c] - values_sorted[f]) * (k - f)


def run_eval():
    rows_out = []
    latencies = []
    grounded_scores = []
    citation_scores = []
    exact_scores = []
    partial_scores = []

    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row["id"]
            question = row["question"]
            gold = row.get("gold_answer", "")

            start = time.perf_counter()
            resp = answer_with_rag(question, k=int(os.getenv("TOP_K", "4")))
            elapsed = (time.perf_counter() - start) * 1000.0  # ms

            answer = resp.get("answer", "")
            grounded = groundedness_heuristic(resp)
            citation_ok = int(has_citations(resp))
            em_pm = exact_partial_match(answer, gold)

            latencies.append(elapsed)
            grounded_scores.append(grounded)
            citation_scores.append(citation_ok)
            exact_scores.append(em_pm["exact_match"])
            partial_scores.append(em_pm["partial_match"])

            rows_out.append({
                "id": qid,
                "question": question,
                "answer": answer,
                "latency_ms": round(elapsed, 2),
                "grounded_heuristic": grounded,
                "citation_present": citation_ok,
                "exact_match": em_pm["exact_match"],
                "partial_match": em_pm["partial_match"],
            })

    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "id", "question", "answer", "latency_ms",
            "grounded_heuristic", "citation_present",
            "exact_match", "partial_match"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    # Aggregate metrics
    grounded_pct = 100.0 * (sum(grounded_scores) / len(grounded_scores)) if grounded_scores else 0.0
    citation_pct = 100.0 * (sum(citation_scores) / len(citation_scores)) if citation_scores else 0.0
    exact_pct = 100.0 * (sum(exact_scores) / len(exact_scores)) if exact_scores else 0.0
    partial_pct = 100.0 * (sum(partial_scores) / len(partial_scores)) if partial_scores else 0.0

    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)

    print("\n=== Evaluation Summary ===")
    print(f"Questions: {len(rows_out)}")
    print(f"Groundedness (heuristic): {grounded_pct:.2f}%")
    print(f"Citation Accuracy proxy (citation present): {citation_pct:.2f}%")
    print(f"Exact Match (optional): {exact_pct:.2f}%")
    print(f"Partial Match (optional): {partial_pct:.2f}%")
    print(f"Latency p50: {p50:.2f} ms")
    print(f"Latency p95: {p95:.2f} ms")
    print(f"Detailed results written to: {OUT_PATH}")


if __name__ == "__main__":
    run_eval()
