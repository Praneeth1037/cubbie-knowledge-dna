"""Offline adaptive diagnostics. One JSON request on stdin, one compact JSON reply."""
from __future__ import annotations

import ast
import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import re
import sys
import uuid
from datetime import datetime, timezone

try:
    from .knowledge_graph import KnowledgeGraph, DATA_DIR
except ImportError:
    from knowledge_graph import KnowledgeGraph, DATA_DIR


class InputError(ValueError):
    def __init__(self, message: str, code: str = "invalid_input"):
        super().__init__(message)
        self.code = code


def parse_answer(answer):
    """Parse numbers/vectors/matrices without eval, arithmetic execution or LLM grading."""
    if isinstance(answer, str):
        if len(answer) > 2000:
            raise ValueError("Answer is too long")
        value = answer.strip().strip("`").strip()
        value = re.sub(r"^(?:the\s+)?(?:answer|output|result)\s*(?:is|=|:)\s*", "", value,
                       flags=re.IGNORECASE).strip()
        if re.fullmatch(r"[+-]?\d+\s*/\s*[+-]?\d+", value):
            answer = float(Fraction(value.replace(" ", "")))
        else:
            answer = ast.literal_eval(value)

    def normalize(value, depth=0):
        if depth > 2:
            raise ValueError("Use a scalar, vector, or matrix")
        if isinstance(value, bool):
            raise ValueError("Booleans are not mathematical answers")
        if isinstance(value, (int, float)):
            if not math.isfinite(value) or abs(value) > 1e12:
                raise ValueError("Use a finite number with magnitude <= 1e12")
            return float(value)
        if isinstance(value, (list, tuple)) and 0 < len(value) <= 16:
            return [normalize(item, depth + 1) for item in value]
        raise ValueError("Use numbers, vectors, or matrices")

    return normalize(answer)


def equivalent(actual, expected, tolerance=1e-6) -> bool:
    if isinstance(expected, list):
        return (isinstance(actual, list) and len(actual) == len(expected)
                and all(equivalent(a, b, tolerance) for a, b in zip(actual, expected)))
    return (not isinstance(actual, list)
            and math.isclose(actual, expected, abs_tol=tolerance, rel_tol=tolerance))


def evaluate(question: dict, answer, misconceptions: dict) -> dict:
    try:
        parsed = parse_answer(answer)
    except (ValueError, SyntaxError, TypeError, ZeroDivisionError, OverflowError, RecursionError):
        return {"verdict": "unscored", "misconception": None,
                "message": "Please give a number, fraction, vector [a,b], or matrix [[a,b],[c,d]]. I haven't scored that answer."}
    if equivalent(parsed, question["expected"], question.get("tolerance", 1e-6)):
        return {"verdict": "correct", "misconception": None,
                "message": "That calculation is correct."}
    for pattern in question.get("patterns", []):
        if equivalent(parsed, pattern["answer"], question.get("tolerance", 1e-6)):
            return {"verdict": "incorrect", "misconception": pattern["misconception"],
                    "message": "That result suggests a possible pattern; let's check it with a different example."}
    return {"verdict": "incorrect", "misconception": None,
            "message": "That result differs from the expected value. Let's check the underlying operation."}


def validate_canvas(context) -> dict:
    if context is None:
        context = {"status": "not_requested"}
    if not isinstance(context, dict):
        raise InputError("canvas must be an object")
    status = context.get("status", "not_requested")
    if status not in {"connected", "disconnected", "unavailable", "no_matches", "not_requested"}:
        raise InputError("Unsupported Canvas status")
    materials = context.get("materials", [])
    if not isinstance(materials, list) or len(materials) > 5:
        raise InputError("Pass at most five Canvas material references")
    cleaned = []
    for item in materials:
        if not isinstance(item, dict) or not isinstance(item.get("title"), str):
            raise InputError("Each Canvas material needs a title")
        url = item.get("url", "")
        if not isinstance(url, str) or (url and not url.startswith("https://")):
            raise InputError("Canvas reference URLs must be HTTPS")
        cleaned.append({"title": item["title"][:120], "url": url[:300]})
    if status != "connected" and cleaned:
        raise InputError("Only connected Canvas context can include materials")
    return {"status": status, "materials": cleaned,
            "source": "course_materials" if status == "connected" and cleaned else "bundled_examples"}


class DiagnosticEngine:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.graph = KnowledgeGraph.load(data_dir / "transformer_concepts.json")
        bank = json.loads((data_dir / "diagnostic_questions.json").read_text())
        self.questions = {q["id"]: q for q in bank["questions"]}
        if len(self.questions) != len(bank["questions"]):
            raise ValueError("Duplicate question ID")
        self.misconceptions = json.loads((data_dir / "misconception_bank.json").read_text())["misconceptions"]
        for concept in self.graph.nodes:
            for role in ("diagnostic", "reassessment", "transfer"):
                if not self.bank(concept, role):
                    raise ValueError(f"Missing {role} questions for {concept}")
            if len(self.bank(concept, "diagnostic")) < 3:
                raise ValueError(f"Need three independent diagnostics for {concept}")
            if "lesson" not in self.graph.nodes[concept]:
                raise ValueError(f"Missing lesson for {concept}")
        for question in self.questions.values():
            self.graph.resolve(question["concept"])
            parse_answer(question["expected"])
            for pattern in question.get("patterns", []):
                if pattern["misconception"] not in self.misconceptions:
                    raise ValueError("Unknown misconception")

    def bank(self, concept, role):
        return [q for q in self.questions.values() if q["concept"] == concept and q["role"] == role]

    def evidence(self, profile, concept):
        return [profile["observations"][i] for i in profile["session"]["evidence"]
                if profile["observations"][i]["concept"] == concept
                and profile["observations"][i]["role"] == "diagnostic"
                and profile["observations"][i]["verdict"] != "unscored"]

    def demonstrated(self, profile, concept):
        return profile["concepts"].get(concept, {}).get("status") == "demonstrated"

    def classify(self, profile, concept):
        evidence = self.evidence(profile, concept)
        correct = sum(e["verdict"] == "correct" for e in evidence)
        wrong = len(evidence) - correct
        if correct and (not wrong or correct >= 2):
            status = "demonstrated"
        elif correct and wrong and len(evidence) >= 3:
            status = "uncertain"
        elif wrong >= 2 and not correct and all(
                self.demonstrated(profile, p) for p in self.graph.nodes[concept]["prerequisites"]):
            status = "likely_gap"
        else:
            status = "suspected" if evidence else "untested"
        profile["concepts"][concept] = {
            "status": status, "evidence_question_ids": [e["question_id"] for e in evidence],
            "basis": "Limited practice evidence; not a claim of durable mastery.",
        }
        return status

    def set_question(self, session, question):
        session["next"] = {"kind": "question", "question_id": question["id"],
                           "concept": question["concept"], "phase": question["role"],
                           "prompt": question["prompt"]}

    def finish(self, session, reason, uncertain=False):
        session["state"] = "uncertain" if uncertain else "complete"
        session["next"] = {"kind": session["state"], "reason": reason}

    def schedule(self, profile):
        session = profile["session"]

        def consider(concept):
            if self.demonstrated(profile, concept):
                return False
            evidence = self.evidence(profile, concept)
            # A failed application routes down the graph before it can become a gap.
            if any(e["verdict"] == "incorrect" for e in evidence):
                prerequisites = self.graph.prerequisites(concept)
                # A matched error pattern is a routing hint, never a diagnosis by itself.
                for observation in reversed(evidence):
                    pattern = self.misconceptions.get(observation["misconception"], {})
                    candidate = pattern.get("suspected_concept")
                    if candidate in prerequisites and consider(candidate):
                        return True
                for dependency in self.graph.nodes[concept]["prerequisites"]:
                    if consider(dependency):
                        return True
            status = self.classify(profile, concept)
            if status == "demonstrated":
                return False
            session["focus"] = concept
            if status == "uncertain":
                self.finish(session, "Inconsistent answers: more evidence is needed; no gap is declared.", True)
                return True
            if status == "likely_gap":
                session["state"] = "intervention"
                session["next"] = {"kind": "intervention", "concept": concept,
                                   "lesson": self.graph.nodes[concept]["lesson"]}
                return True
            used = {e["question_id"] for e in evidence}
            remaining = [q for q in self.bank(concept, "diagnostic") if q["id"] not in used]
            if not remaining:
                self.finish(session, "The question bank is exhausted without a reliable diagnosis.", True)
            else:
                self.set_question(session, remaining[0])
            return True

        if session.get("focus") and consider(session["focus"]):
            return
        for concept in session["scope"]:
            if consider(concept):
                return
        self.finish(session, "All concepts in this target's scope have practice evidence of understanding.")

    def start(self, profile, request):
        target = self.graph.resolve(request.get("target", "transformer_attention"))
        canvas = validate_canvas(request.get("canvas"))
        prior = profile.get("session")
        if prior and request["action"] == "start":
            if prior["target"] != target:
                raise InputError("Use restart to change the target of an existing session")
            return
        if prior:
            profile["session_history"].append(copy.deepcopy(prior))
        session = {"id": uuid.uuid4().hex, "target": target, "state": "diagnostic",
                   "scope": self.graph.learning_order(target), "evidence": [],
                   "focus": None, "canvas": canvas, "next": None}
        profile["session"] = session
        # Reset unresolved conclusions for a fresh diagnostic pass, retain demonstrations.
        for concept in session["scope"]:
            if not self.demonstrated(profile, concept):
                profile["concepts"][concept] = {"status": "untested", "evidence_question_ids": []}
        probe = "attention_output" if target == "transformer_attention" else target
        if not self.demonstrated(profile, probe):
            session["focus"] = probe
            self.set_question(session, self.bank(probe, "diagnostic")[0])
        else:
            self.schedule(profile)

    def validate_turn(self, profile, request):
        session = profile.get("session")
        if not session:
            raise InputError("Start a session first")
        revision = request.get("revision")
        if (request.get("session_id") != session["id"] or type(revision) is not int
                or revision != profile["revision"]):
            raise InputError("This turn is stale. Resume to get the current session and revision.", "stale_turn")
        return session

    def answer(self, profile, request):
        session = self.validate_turn(profile, request)
        pending = session["next"]
        if pending["kind"] != "question" or request.get("question_id") != pending["question_id"]:
            raise InputError("Answer only the current pending question", "stale_turn")
        if "answer" not in request:
            raise InputError("answer is required")
        raw = request["answer"]
        if len(json.dumps(raw)) > 4000:
            raise InputError("Answer exceeds 4000 JSON characters")
        question = self.questions[pending["question_id"]]
        result = evaluate(question, raw, self.misconceptions)
        observation = {"session_id": session["id"], "observed_at": datetime.now(timezone.utc).isoformat(),
                       "question_id": question["id"],
                       "concept": question["concept"], "role": question["role"],
                       "answer": raw, "verdict": result["verdict"],
                       "misconception": result["misconception"]}
        profile["observations"].append(observation)
        session["evidence"].append(len(profile["observations"]) - 1)
        session["feedback"] = result
        concept = question["concept"]
        if result["verdict"] == "unscored":
            attempts = [profile["observations"][i] for i in session["evidence"]
                        if profile["observations"][i]["question_id"] == question["id"]
                        and profile["observations"][i]["verdict"] == "unscored"]
            if len(attempts) >= 2:
                self.finish(session, "Two answers could not be scored. Understanding remains uncertain.", True)
            return
        if question["role"] == "diagnostic":
            session["focus"] = concept
            self.classify(profile, concept)
            self.schedule(profile)
            return
        intervention = profile["interventions"][-1]
        outcome = {"question_id": question["id"], "verdict": result["verdict"]}
        intervention[question["role"]] = outcome
        if result["verdict"] != "correct":
            if question["role"] == "reassessment":
                profile["concepts"][concept]["status"] = "needs_practice"
            intervention["outcome"] = "not_yet_verified"
            session["feedback"]["message"] = question["explanation"] + " Let's revisit this in another session."
            self.finish(session, "The fresh check did not verify full improvement; more practice is recommended.")
        elif question["role"] == "reassessment":
            profile["concepts"][concept] = {
                "status": "demonstrated", "evidence_question_ids": [question["id"]],
                "basis": "Fresh reassessment passed; transfer is checked separately.",
            }
            self.set_question(session, self.bank(concept, "transfer")[0])
        else:
            intervention["outcome"] = "improvement_verified"
            profile["concepts"][concept]["evidence_question_ids"].append(question["id"])
            self.finish(session, "Improvement verified on fresh reassessment and Transformer transfer; other concepts may remain untested.")

    def teach(self, profile, request):
        session = self.validate_turn(profile, request)
        pending = session["next"]
        if pending["kind"] != "intervention" or request.get("concept") != pending["concept"]:
            raise InputError("No matching intervention is pending")
        concept = pending["concept"]
        profile["interventions"].append({"session_id": session["id"], "concept": concept,
                                         "delivered_at": datetime.now(timezone.utc).isoformat(),
                                         "lesson_delivered": True, "outcome": "pending",
                                         "reassessment": None, "transfer": None})
        session["state"] = "reassessment"
        session.pop("feedback", None)
        self.set_question(session, self.bank(concept, "reassessment")[0])

    def transition(self, profile, request):
        if not isinstance(request, dict):
            raise InputError("Request must be a JSON object")
        action = request.get("action")
        if action in {"start", "restart"}:
            self.start(profile, request)
        elif action == "answer":
            self.answer(profile, request)
        elif action == "teach":
            self.teach(profile, request)
        elif action not in {"resume", "profile"}:
            raise InputError("action must be start, restart, resume, answer, teach, or profile")
        return profile

    def report(self, profile):
        try:
            from .profile_store import summarize
        except ImportError:
            from profile_store import summarize
        session = profile.get("session")
        if not session:
            return {"ok": True, "revision": profile["revision"], "session_id": None,
                    "next": {"kind": "not_started", "reason": "No learning history; start a session."},
                    "diagnosis": None, "summary": summarize(profile)}
        concept = session.get("focus")
        evidence = self.evidence(profile, concept) if concept else []
        status = profile["concepts"].get(concept, {}).get("status", "untested")
        counts = {}
        for item in evidence:
            if item["misconception"]:
                key = item["misconception"]
                counts[key] = counts.get(key, 0) + 1
        diagnosis = {
            "concept": concept, "status": status,
            "confidence": "moderate" if status == "likely_gap" else "limited",
            "evidence_question_ids": [e["question_id"] for e in evidence],
            "observations": [{"question_id": e["question_id"], "verdict": e["verdict"],
                              "pattern_match": e["misconception"]} for e in evidence],
            "assumptions": (["These errors may reflect a conceptual gap rather than a slip; the lesson and fresh checks test this."]
                            if status == "likely_gap" else []),
            "misconception_hypotheses": [{"id": key, "supporting_answers": count,
                                           "description": self.misconceptions[key]["description"]}
                                          for key, count in counts.items()],
        }
        result = {"ok": True, "session_id": session["id"], "revision": profile["revision"],
                  "next": session["next"], "diagnosis": diagnosis,
                  "summary": summarize(profile), "canvas": session["canvas"]}
        if session.get("feedback"):
            result["feedback"] = session["feedback"]
        return result


def reject_nonfinite(value):
    raise InputError(f"Nonfinite JSON value: {value}")


def main():
    try:
        try:
            from .profile_store import ProfileStore, StoreError
        except ImportError:
            from profile_store import ProfileStore, StoreError
        raw = sys.stdin.read(16001)
        if len(raw) > 16000:
            raise InputError("Request exceeds 16000 characters")
        request = json.loads(raw, parse_constant=reject_nonfinite)
        if not isinstance(request, dict):
            raise InputError("Request must be a JSON object")
        engine = DiagnosticEngine()
        store = ProfileStore()
        learner = request.get("learner_id", "student")
        if request.get("action") in {"resume", "profile"}:
            profile = store.load(learner)
        else:
            profile = store.update(learner, lambda p: engine.transition(p, request))
        output = json.dumps(engine.report(profile), ensure_ascii=False, allow_nan=False)
        if len(output) > 8000:
            raise InputError("Report exceeds the host read limit", "report_too_large")
        print(output)
    except (InputError, ValueError, OSError, KeyError, TypeError, StoreError) as exc:
        code = getattr(exc, "code", "io_error" if isinstance(exc, OSError) else "invalid_input")
        print(json.dumps({"ok": False, "error": {"code": code, "message": str(exc)}}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
