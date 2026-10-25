"""Knowledge DNA 3.0: pure, bounded, hypothesis-driven learning investigations."""
import copy
import json
from pathlib import Path
import uuid

try:
    from .answer_evaluator import evaluate
    from .hypothesis_engine import initialize, update, conclusion
    from .question_selector import select
    from .knowledge_graph import KnowledgeGraph
    from .evidence_engine import prepare, prioritize
except ImportError:
    from answer_evaluator import evaluate
    from hypothesis_engine import initialize, update, conclusion
    from question_selector import select
    from knowledge_graph import KnowledgeGraph
    from evidence_engine import prepare, prioritize

DATA = Path(__file__).resolve().parent.parent / "data"
VERSION = "3.0"


class InvestigationError(ValueError):
    def __init__(self, message, code="invalid_input"):
        super().__init__(message)
        self.code = code


class InvestigationEngine:
    def __init__(self):
        bank = json.loads((DATA / "attention_questions.json").read_text())
        self.questions = {q["id"]: q for q in bank["questions"]}
        if len(self.questions) != len(bank["questions"]):
            raise ValueError("Question IDs must be unique")
        self.repairs = bank["repairs"]
        self.patterns = json.loads((DATA / "hypothesis_patterns.json").read_text())["hypotheses"]
        self.graph = KnowledgeGraph.load(DATA / "forensics_concepts.json")

    def start(self, request):
        scenario = request.get("scenario", "attention")
        if scenario not in {"attention", "false_mastery", "academic_forensics", "writing"}:
            raise InvestigationError("scenario must be attention, false_mastery, academic_forensics, or writing")
        budget = request.get("question_budget", 8)
        if type(budget) is not int or not 3 <= budget <= 10:
            raise InvestigationError("question_budget must be an integer from 3 to 10")
        domain = "writing" if scenario == "writing" else ("shapes" if scenario == "academic_forensics" else "attention")
        exposed = request.get("exposed_questions", [])
        if not isinstance(exposed, list) or len(exposed) > 30 or any(not isinstance(q, str) or q not in self.questions for q in exposed):
            raise InvestigationError("exposed_questions must contain at most 30 known question IDs")
        if "initial_exposed" in request and type(request["initial_exposed"]) is not bool:
            raise InvestigationError("initial_exposed must be boolean")
        if request.get("initial_exposed"):
            exposed = exposed + [{"attention": "attention_initial", "writing": "writing_initial", "shapes": "shape_initial"}[domain]]
        exposed = list(dict.fromkeys(exposed))
        if len(exposed) > 30:
            raise InvestigationError("At most 30 exposed question IDs are supported")
        connections, sources = prepare(request, self.patterns, domain)
        session = {"version": 3, "id": uuid.uuid4().hex, "scenario": scenario, "domain": domain,
                   "goal": "Clear paragraph arguments" if domain == "writing" else ("Tensor implementation" if domain == "shapes" else "Transformer attention"),
                   "budget": budget, "observations": [], "hypotheses": initialize(self.patterns, domain),
                   "conclusion": None, "repair": None, "understanding": {}, "sources": sources,
                   "connections": connections,
                   "message_ids": [], "false_mastery": False, "next": None, "notice": None,
                   "exposed_questions": list(dict.fromkeys(exposed))}
        qid = "recall_qkv" if scenario == "false_mastery" else self.opening_id(session)
        prioritize(session["hypotheses"], sources)
        if domain == "shapes":
            top = max(session["hypotheses"], key=lambda h: session["hypotheses"][h]["score"])
            qid = {"broadcasting": "broadcast_probe", "notation_to_code": "implementation_probe"}.get(top, "shape_initial")
        self.assign(session, qid, {"reason": "Establish the initial observation without explaining the answer."})
        if sources:
            session["next"]["selection"].update(source_ids=[s["id"] for s in sources],
                                                reason="Use source-derived priors to choose a live test; the records alone do not establish a gap.")
        return session

    def validate(self, session):
        if (not isinstance(session, dict) or session.get("version") != 3
                or not isinstance(session.get("id"), str)
                or session.get("domain") not in {"attention", "shapes", "writing"}
                or type(session.get("budget")) is not int or not 3 <= session["budget"] <= 10
                or not isinstance(session.get("observations"), list) or len(session["observations"]) > 16
                or not isinstance(session.get("hypotheses"), dict)
                or not isinstance(session.get("next"), dict)):
            raise InvestigationError("Malformed investigation; preserve the original record.", "corrupt_profile")
        required = {"goal": str, "scenario": str, "sources": list, "connections": dict,
                    "message_ids": list, "understanding": dict, "false_mastery": bool}
        if any(type(session.get(key)) is not value for key, value in required.items()):
            raise InvestigationError("Invalid investigation fields", "corrupt_profile")
        expected_hypotheses = {key for key, value in self.patterns.items() if value["domain"] == session["domain"]}
        exposed = session.get("exposed_questions", [])
        if not isinstance(exposed, list) or len(exposed) > 30 or any(not isinstance(q, str) or q not in self.questions for q in exposed):
            raise InvestigationError("Invalid exposed-question record", "corrupt_profile")
        if set(session["hypotheses"]) != expected_hypotheses:
            raise InvestigationError("Unexpected hypothesis set", "corrupt_profile")
        levels = {"not demonstrated", "partially demonstrated", "demonstrated on diagnostic examples",
                  "demonstrated on independent examples", "demonstrated in a new application"}
        if any(not isinstance(value, str) or value not in levels for value in session["understanding"].values()):
            raise InvestigationError("Unsupported understanding claim", "corrupt_profile")
        kind = session["next"].get("kind")
        if not isinstance(kind, str) or kind not in {"question", "intervention", "complete", "uncertain"}:
            raise InvestigationError("Invalid next action", "corrupt_profile")
        if kind == "question" and session["next"].get("question_id") not in self.questions:
            raise InvestigationError("Unknown pending question", "corrupt_profile")
        if "repair" not in session or (session["repair"] is not None and
                (not isinstance(session["repair"], dict) or session["repair"].get("id") not in self.repairs
                 or any(k not in session["repair"] for k in ("delivered", "practice", "independent", "transfer")))):
            raise InvestigationError("Invalid intervention record", "corrupt_profile")
        if len(session["sources"]) > 6 or len(session["message_ids"]) > 16:
            raise InvestigationError("History exceeds retention bounds", "corrupt_profile")
        try:
            prepare({"connections": session["connections"], "sources": session["sources"],
                     "evidence_authorized": True, "synthetic_mode": True}, self.patterns, session["domain"])
        except (ValueError, TypeError, KeyError) as exc:
            raise InvestigationError("Malformed academic provenance", "corrupt_profile") from exc
        seen = set()
        for item in session["observations"]:
            if (not isinstance(item, dict) or item.get("question_id") not in self.questions
                    or item.get("verdict") not in {"correct", "incorrect", "incomplete", "unscored", "partial"}):
                raise InvestigationError("Malformed observation", "corrupt_profile")
            if item["question_id"] in seen or "answer" not in item or "updates" not in item:
                raise InvestigationError("Duplicate or incomplete observation", "corrupt_profile")
            seen.add(item["question_id"])
        for key, record in session["hypotheses"].items():
            if (key not in self.patterns or not isinstance(record, dict)
                    or type(record.get("score")) is not int
                    or not isinstance(record.get("support"), list)
                    or not isinstance(record.get("against"), list)):
                raise InvestigationError("Malformed hypothesis ledger", "corrupt_profile")
        return session

    def assign(self, session, qid, reason):
        if qid not in self.questions:
            raise InvestigationError(f"Unknown question: {qid}")
        if qid in session.get("exposed_questions", []):
            raise InvestigationError("This item was previously exposed; choose unfamiliar material.", "question_bank_exhausted")
        if any(o["question_id"] == qid for o in session["observations"]):
            raise InvestigationError("A question cannot be repeated in an investigation")
        session["next"] = {"kind": "question", "question_id": qid, "selection": reason}

    def finish(self, session, reason, uncertain=False):
        session["next"] = {"kind": "uncertain" if uncertain else "complete", "reason": reason}

    def lesson(self, session, repair, requested=False):
        session["repair"] = {"id": repair, "delivered": False, "requested_directly": requested,
                             "practice": None, "independent": None, "transfer": None}
        session["next"] = {"kind": "intervention", "repair_id": repair}

    def investigate(self, session):
        decision = conclusion(session, self.questions)
        if decision and decision["status"] == "no_gap_demonstrated" and session.get("investigation_trigger"):
            decision = None  # A failed independent check defeats a premature no-gap finding.
        if decision:
            session["conclusion"] = decision
            if decision["status"] == "supported":
                self.lesson(session, self.patterns[decision["hypothesis"]]["repair"])
                return
            if decision["status"] == "no_gap_demonstrated":
                self.assign(session, self.assessment_id(session, "independent"), {"reason": "Current checks worked; independently change the conditions."})
                return
            self.finish(session, decision["language"], True)
            return
        used = sum(self.questions[o["question_id"]]["role"] == "diagnostic" for o in session["observations"])
        if used >= session["budget"]:
            session["conclusion"] = {"status": "uncertain", "hypothesis": None, "basis": [],
                                     "language": "Question budget exhausted; competing explanations remain."}
            self.finish(session, session["conclusion"]["language"], True)
            return
        question, why = select(session, self.questions, self.graph)
        if not question:
            session["conclusion"] = {"status": "uncertain", "hypothesis": None, "basis": [],
                                     "language": "Mixed or insufficient evidence; no reliable cause established."}
            self.finish(session, session["conclusion"]["language"], True)
        else:
            self.assign(session, question["id"], why)

    def answer(self, session, request):
        pending = session["next"]
        if pending["kind"] != "question" or request.get("question_id") != pending["question_id"]:
            raise InvestigationError("Only answer the pending question", "stale_turn")
        if "answer" not in request or len(json.dumps(request["answer"])) > 3200:
            raise InvestigationError("Provide a bounded answer")
        message_id = request.get("message_id")
        if message_id is not None:
            if not isinstance(message_id, str) or len(message_id) > 80:
                raise InvestigationError("message_id must be at most 80 characters")
            if message_id in session["message_ids"]:
                raise InvestigationError("This student message was already processed", "stale_turn")
            session["message_ids"].append(message_id)
        question = self.questions[pending["question_id"]]
        scoring = evaluate(question, request["answer"])
        changes = update(session["hypotheses"], question, scoring)
        session["observations"].append({"question_id": question["id"], "answer": request["answer"],
                                         "verdict": scoring["verdict"], "signal": scoring["signal"],
                                         "updates": changes, "rubric_hits": scoring.get("rubric_hits")})
        session["feedback"] = scoring["message"]
        reductions = [c for c in changes if c["delta"] < 0]
        if reductions:
            description = self.patterns[reductions[0]["hypothesis"]]["description"]
            session["revision_message"] = "This correct check makes the following explanation less likely: " + description
            if reductions[0]["hypothesis"] == "scalar_multiplication":
                session["revision_message"] = "You multiplied the vector correctly. A scalar-multiplication gap is less likely; let's check combining values or reporting the result."
        else:
            session.pop("revision_message", None)
        role = question["role"]
        application_key = "paragraph_application" if session["domain"] == "writing" else "calculation"
        if role == "recall":
            session["understanding"]["verbal_recall"] = self.level(scoring, "demonstrated on diagnostic examples")
            session["feedback"] = "Definitions are recall evidence. Next we will check application."
            self.assign(session, self.opening_id(session), {"reason": "Recall does not establish calculation ability."})
        elif role == "diagnostic":
            if session["domain"] == "shapes":
                self.investigate(session)
            elif question.get("opening") and scoring["verdict"] == "correct":
                session["understanding"][application_key] = "demonstrated on diagnostic examples"
                session["conclusion"] = {"status": "no_gap_demonstrated", "hypothesis": None,
                                         "basis": [question["id"]], "language": "The initial example worked; independent verification follows."}
                self.assign(session, self.assessment_id(session, "independent"), {"reason": "Change the context to check an independent example."})
            else:
                if question.get("opening") and session["understanding"].get("verbal_recall") == "demonstrated on diagnostic examples":
                    session["false_mastery"] = True
                    session["feedback"] = "Your definitions worked; application has not yet been demonstrated. Let's test the operations."
                self.investigate(session)
        elif role == "practice":
            session["repair"]["practice"] = scoring["verdict"]
            if scoring["verdict"] == "correct":
                self.assign(session, self.assessment_id(session, "independent"), {"reason": "Practice succeeded; now change the conditions independently."})
            else:
                self.finish(session, "Practice has not succeeded yet; independent improvement is not verified.")
        elif role == "verification":
            session["understanding"][application_key] = self.level(scoring, "demonstrated on independent examples")
            if session["repair"]:
                session["repair"]["independent"] = scoring["verdict"]
            if scoring["verdict"] == "correct":
                self.assign(session, self.assessment_id(session, "transfer"), {"reason": "An independent answer does not establish transfer to a new application."})
            elif not session["repair"]:
                session["conclusion"] = None
                session["investigation_trigger"] = question["id"]
                session["feedback"] = "That independent check did not work. It changes the earlier picture; let's investigate the cause before teaching."
                self.investigate(session)
            else:
                self.finish(session, "The independent example did not verify improvement. More focused practice is recommended.")
        elif role == "transfer":
            session["understanding"]["transfer"] = self.level(scoring, "demonstrated in a new application")
            if session["repair"]:
                session["repair"]["transfer"] = scoring["verdict"]
            self.finish(session, "Independent and transfer observations recorded; no permanent mastery claim is made.")

    @staticmethod
    def level(scoring, success):
        if scoring["verdict"] == "correct":
            return success
        return "partially demonstrated" if scoring["verdict"] in {"partial", "incomplete"} else "not demonstrated"

    def opening_id(self, session):
        candidates = ["writing_initial", "writing_fresh_initial"] if session["domain"] == "writing" else ["attention_initial", "attention_fresh_initial"]
        if session["domain"] == "shapes":
            return "shape_initial"
        return self.unused_id(session, candidates)

    @staticmethod
    def unused_id(session, candidates):
        used = {o["question_id"] for o in session["observations"]} | set(session.get("exposed_questions", []))
        for candidate in candidates:
            if candidate not in used:
                return candidate
        raise InvestigationError("No unused independent item remains; start a new investigation with unfamiliar material.", "question_bank_exhausted")

    def assessment_id(self, session, role):
        if session["domain"] == "attention":
            return "transfer_attention" if role == "transfer" else self.unused_id(session, ["independent_attention", "independent_attention_followup"])
        if session["domain"] == "writing":
            if role == "transfer":
                return "writing_transfer"
            repair = (session.get("repair") or {}).get("id")
            first = {"writing_claim": "writing_independent_claim", "writing_evidence": "writing_independent_evidence"}.get(repair, "writing_independent")
            return self.unused_id(session, [first, "writing_independent_followup"])
        if role == "transfer":
            return "transfer_shapes"
        repair = (session.get("repair") or {}).get("id")
        return {"broadcasting": "independent_broadcast", "notation_to_code": "independent_implementation"}.get(repair, "independent_shapes")

    def apply(self, session, request):
        session = copy.deepcopy(self.validate(session))
        action = request["action"]
        if action == "answer":
            self.answer(session, request)
        elif action == "repair":
            if session["next"]["kind"] != "intervention":
                raise InvestigationError("No lesson is pending")
            session["repair"]["delivered"] = True
            practice = {"scalar_multiplication": "practice_scalar", "vector_addition": "practice_addition",
                        "response_format": "practice_format", "tensor_shapes": "practice_shapes",
                        "broadcasting": "practice_broadcast", "notation_to_code": "practice_implementation",
                        "writing_claim": "writing_practice_claim", "writing_evidence": "writing_practice_evidence",
                        "writing_link": "writing_practice_link"}.get(session["repair"]["id"], "practice_weighted")
            self.assign(session, practice, {"reason": "Try a different example after the delivered targeted lesson."})
        elif action == "skip":
            if session["next"]["kind"] != "question":
                raise InvestigationError("Skip is available while answering questions")
            session["conclusion"] = {"status": "insufficient_evidence", "hypothesis": None, "basis": [],
                                     "language": "Student requested an explanation; no cause was diagnosed."}
            self.lesson(session, "writing_link" if session["domain"] == "writing" else "weighted_sums", requested=True)
        elif action == "verify":
            self.assign(session, self.assessment_id(session, "independent"), {"reason": "Student requested an independent check; no new diagnosis is inferred."})
        else:
            raise InvestigationError("Unsupported mutation")
        return session

    def report(self, session, full=False):
        self.validate(session)
        pending = copy.deepcopy(session["next"])
        if pending["kind"] == "question":
            q = self.questions[pending["question_id"]]
            pending.update(prompt=q["prompt"], phase=q["role"], concept=q["concept"])
        elif pending["kind"] == "intervention":
            pending["lesson"] = self.repairs[pending["repair_id"]]
        repair = session["repair"]
        decision = session["conclusion"] or {}
        next_step = ("Try a new masking case with tensor axes labeled before writing code." if session["domain"] == "shapes"
                     else ("Try an unfamiliar paragraph with a point, evidence and an explanation." if session["domain"] == "writing"
                           else "Try query-key scores or softmax next; those are outside this investigation's checks."))
        if pending["kind"] == "uncertain":
            next_step = "Talk through one conflicting answer; keep the cause uncertain until another independent check."
        elif session["understanding"].get("transfer") in {"partially demonstrated", "not demonstrated"}:
            next_step = ("Explain why a detail supports the main point in a fresh paragraph." if session["domain"] == "writing"
                         else "Practice explaining how attention weights mix values, then use a fresh transfer prompt.")
        elif session["understanding"].get("calculation") == "not demonstrated":
            next_step = "Revisit " + (repair or {}).get("id", "weighted sums") + " with a different numerical example."
        elif repair and repair["independent"] == "correct":
            next_step = "Recheck " + repair["id"] + " in a later session, then continue toward " + session["goal"] + "."
        report = {"original_goal": session["goal"], "diagnosis": session["conclusion"],
                  "observed_difficulty": decision.get("observed_pattern", self.patterns[decision["hypothesis"]]["description"]) if decision.get("hypothesis") else "No specific cause established by the available observations.",
                  "understanding": session["understanding"], "intervention": repair,
                  "improvement_verified": bool(repair and repair["delivered"] and repair["independent"] == "correct" and repair["transfer"] == "correct"),
                  "recall_application_mismatch": session["false_mastery"],
                  "diagnostic_questions_used": sum(self.questions[o["question_id"]]["role"] == "diagnostic" for o in session["observations"]),
                  "next_step": next_step}
        result = {"ok": True, "engine": "knowledge-dna", "engine_version": VERSION,
                  "session_id": session["id"], "next": pending, "report": report,
                  "feedback": session.get("feedback", "Let's investigate with short, discriminating checks."),
                  "revision_message": session.get("revision_message"),
                  "hypotheses": [{"id": key, "score": h["score"],
                                   "status": "supported" if decision.get("hypothesis") == key else ("less_supported" if h["score"] < 0 else "under_consideration")}
                                  for key, h in session["hypotheses"].items()]}
        result["academic_evidence"] = {"sources_used": len(session["sources"]),
                                       "synthetic": bool(session["sources"] and session["sources"][0]["synthetic"]),
                                       "connections": session["connections"]}
        result["last_observation"] = {k: session["observations"][-1][k] for k in ("question_id", "verdict", "signal")} if session["observations"] else None
        if full:
            result["investigation"] = {
                "hypotheses": [{"id": key, "description": self.patterns[key]["description"],
                                 "for": h["support"], "against": h["against"],
                                 "source_priors": h.get("source_support", [])} for key, h in session["hypotheses"].items()],
                "path": [{"question_id": o["question_id"], "answer": str(o["answer"])[:90],
                          "verdict": o["verdict"]} for o in session["observations"]],
                "sources": session["sources"], "connections": session["connections"],
            }
            result["investigation"]["assessments"] = [
                {"question_id": o["question_id"], "role": self.questions[o["question_id"]]["role"],
                 "answer_excerpt": str(o["answer"])[:90], "verdict": o["verdict"]}
                for o in session["observations"] if self.questions[o["question_id"]]["role"] in {"practice", "verification", "transfer"}]
        return result
