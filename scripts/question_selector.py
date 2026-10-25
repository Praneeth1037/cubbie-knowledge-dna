"""Choose a safe, unasked experiment using hand-authored categorical predictions."""
from itertools import combinations


def select(session, questions, graph=None):
    seen = {o["question_id"] for o in session["observations"]}
    observed = {o["question_id"]: o for o in session["observations"]}
    hypotheses = session["hypotheses"]
    viable = [key for key, item in hypotheses.items() if item["score"] >= 0]
    if not viable:
        viable = list(hypotheses)
    candidates = []
    for question in questions.values():
        if (question["domain"] != session["domain"] or question["role"] != "diagnostic"
                or question["id"] in seen or question.get("opening")):
            continue
        if question["id"] in session.get("exposed_questions", []):
            continue
        if any(qid not in seen for qid in question.get("requires", [])):
            continue
        prerequisites = graph.prerequisites(question["concept"]) if graph and question["concept"] in graph.nodes else []
        prerequisite_tests = {q["concept"] for q in questions.values() if q.get("direct_test") and q["concept"] in prerequisites}
        observed_concepts = {questions[qid]["concept"] for qid in seen}
        if not prerequisite_tests.issubset(observed_concepts):
            continue
        if question.get("after_error") and observed.get(question["after_error"], {}).get("verdict") not in {"incorrect", "incomplete", "partial"}:
            continue
        opening = next((o for o in session["observations"] if questions[o["question_id"]].get("opening") and questions[o["question_id"]]["role"] == "diagnostic"), {})
        if question["id"] == "dimension" and opening.get("verdict") != "incomplete":
            continue
        predictions = question["predictions"]
        separated = sum((1 + max(0, hypotheses[a]["score"])) * (1 + max(0, hypotheses[b]["score"]))
                        for a, b in combinations(viable, 2)
                        if predictions.get(a, "correct") != predictions.get(b, "correct"))
        coverage = sum(1 + max(0, hypotheses[h]["score"]) for h in question["tests"] if h in viable)
        if not separated and not coverage:
            continue
        score = separated + coverage - 2 * question["difficulty"]
        if question["id"] == "dimension":
            score += 100  # Cheapest structural check when a vector reply is incomplete.
        candidates.append((score, question.get("priority", 0), question["id"], separated, coverage))
    if not candidates:
        return None, {"reason": "No unused discriminating experiment remains."}
    score, _, qid, separated, coverage = sorted(candidates, key=lambda c: (-c[0], -c[1], c[2]))[0]
    return questions[qid], {"reason": "Distinguish remaining explanations with an unasked operation check.",
                            "score": score, "separated_pair_weight": separated,
                            "hypothesis_coverage": coverage, "difficulty_cost": 2 * questions[qid]["difficulty"],
                            "prerequisite_policy": "Isolate graph prerequisites before testing their combination; answered does not mean mastered.",
                            "assumption": "Categorical predictions and ordinal evidence weights are authored heuristics, not probabilities."}
