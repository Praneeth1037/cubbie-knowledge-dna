"""Inspectable ordinal evidence ledger, not statistical probabilities."""


def initialize(patterns, domain):
    return {key: {"support": [], "against": [], "score": 0}
            for key, spec in patterns.items() if spec["domain"] == domain}


def update(hypotheses, question, scoring):
    changes = []
    rules = question.get("evidence", {})
    effects = rules.get(scoring["signal"], rules.get(scoring["verdict"], {}))
    for key, amount in effects.items():
        if key not in hypotheses:
            continue
        record = hypotheses[key]
        before = record["score"]
        record["score"] += amount
        field = "support" if amount > 0 else "against"
        if question["id"] not in record[field]:
            record[field].append(question["id"])
        changes.append({"hypothesis": key, "delta": amount, "before": before,
                        "after": record["score"], "question_id": question["id"]})
    return changes


def conclusion(session, questions):
    observations = [o for o in session["observations"] if questions[o["question_id"]]["role"] == "diagnostic"]
    by_id = {o["question_id"]: o for o in observations}
    for key, record in session["hypotheses"].items():
        if key in {"incomplete_response", "isolated_error"}:
            continue
        direct = [o for o in observations if key in questions[o["question_id"]].get("tests", [])
                  and questions[o["question_id"]].get("direct_test") == key]
        errors = [o for o in direct if o["verdict"] == "incorrect"]
        correct = [o for o in direct if o["verdict"] == "correct"]
        # Sources and incomplete answers cannot meet this live-evidence requirement.
        if len(errors) >= 2 and not correct and record["score"] >= 4:
            return {"status": "supported", "hypothesis": key,
                    "basis": [o["question_id"] for o in errors],
                    "observed_pattern": ("On two checks, the selected sentence did not explain how the evidence supports the main point."
                                         if key == "writing_link" else
                                         "On two weighted checks, the responses added value vectors without applying their weights."
                                         if key == "weighted_aggregation" and all(o["signal"] == "unweighted" for o in errors)
                                         else "Two distinct checks of this operation were incorrect; the cause remains a likely explanation."),
                    "language": "A likely explanation on these examples; not a personal trait."}
    if session["domain"] == "attention":
        required = ["dimension", "scalar_probe", "addition_probe", "weighted_probe"]
        initial = next((o for o in observations if questions[o["question_id"]].get("opening")), {})
        if all(by_id.get(q, {}).get("verdict") == "correct" for q in required):
            other_errors = [o for o in observations if o["verdict"] == "incorrect"]
            if initial.get("verdict") == "incomplete" and not other_errors:
                return {"status": "supported", "hypothesis": "incomplete_response",
                        "basis": [initial["question_id"]] + required,
                        "language": "The original response was incomplete; tested operations subsequently worked. Intent is unknown."}
            if len(other_errors) == 1 and other_errors[0]["question_id"] == "attention_initial":
                return {"status": "uncertain", "hypothesis": None,
                        "basis": [o["question_id"] for o in observations],
                        "language": "An isolated error remains possible; no stable operational gap was established."}
    elif all(by_id.get(q, {}).get("verdict") == "correct" for q in ("shape_initial", "broadcast_probe", "implementation_probe")):
        if not any(o["verdict"] == "incorrect" for o in observations):
            return {"status": "no_gap_demonstrated", "hypothesis": None,
                    "basis": ["shape_initial", "broadcast_probe", "implementation_probe"],
                    "language": "Current checks worked; past feedback does not establish a present gap."}
    return None
