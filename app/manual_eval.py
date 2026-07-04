import csv
from pathlib import Path

RESULTS_PATH = Path("data/eval/results.csv")
AUDIT_PATH = Path("data/eval/data_eval_manual_audit.csv")


def prefill_audit_from_results():
    """
    Create manual_audit.csv prefilled with question/answer/citations from results.csv
    if file does not already exist.
    """
    if AUDIT_PATH.exists():
        print(f"{AUDIT_PATH} already exists. Skipping prefill.")
        return

    rows = []
    with RESULTS_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "id": r.get("id", ""),
                "question": r.get("question", ""),
                "answer": r.get("answer", ""),
                # results.csv currently does not include raw citations column,
                # so keep blank for manual reference/fill.
                "citations": "",
                "grounded_1_0": "",
                "citation_accurate_1_0": "",
                "completeness_2_1_0": "",
                "concise_1_0": "",
                "notes": "",
            })

    with AUDIT_PATH.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "id", "question", "answer", "citations",
            "grounded_1_0", "citation_accurate_1_0",
            "completeness_2_1_0", "concise_1_0", "notes"
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {AUDIT_PATH}. Fill scoring columns manually, then re-run this script.")


def _safe_int(v, allowed):
    try:
        i = int(str(v).strip())
        return i if i in allowed else None
    except Exception:
        return None


def compute_metrics():
    """
    Compute audited metrics after manual labels are filled.
    """
    if not AUDIT_PATH.exists():
        print(f"{AUDIT_PATH} not found. Run prefill first.")
        return

    total = 0
    grounded_sum = 0
    citation_sum = 0
    concise_sum = 0
    completeness_sum = 0

    grounded_n = citation_n = concise_n = completeness_n = 0

    with AUDIT_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            total += 1

            g = _safe_int(r.get("grounded_1_0", ""), {0, 1})
            c = _safe_int(r.get("citation_accurate_1_0", ""), {0, 1})
            k = _safe_int(r.get("concise_1_0", ""), {0, 1})
            m = _safe_int(r.get("completeness_2_1_0", ""), {0, 1, 2})

            if g is not None:
                grounded_sum += g
                grounded_n += 1
            if c is not None:
                citation_sum += c
                citation_n += 1
            if k is not None:
                concise_sum += k
                concise_n += 1
            if m is not None:
                completeness_sum += m
                completeness_n += 1

    grounded_pct = (100 * grounded_sum / grounded_n) if grounded_n else 0.0
    citation_pct = (100 * citation_sum / citation_n) if citation_n else 0.0
    concise_pct = (100 * concise_sum / concise_n) if concise_n else 0.0
    completeness_avg = (completeness_sum / completeness_n) if completeness_n else 0.0

    print("\n=== Manual Audit Summary ===")
    print(f"Rows in audit file: {total}")
    print(f"Scored groundedness rows: {grounded_n}")
    print(f"Scored citation-accuracy rows: {citation_n}")
    print(f"Scored completeness rows: {completeness_n}")
    print(f"Scored conciseness rows: {concise_n}")
    print(f"Groundedness (manual): {grounded_pct:.2f}%")
    print(f"Citation Accuracy (manual): {citation_pct:.2f}%")
    print(f"Completeness avg (0-2): {completeness_avg:.2f}")
    print(f"Conciseness: {concise_pct:.2f}%")
    print("================================")


if __name__ == "__main__":
    prefill_audit_from_results()
    compute_metrics()
