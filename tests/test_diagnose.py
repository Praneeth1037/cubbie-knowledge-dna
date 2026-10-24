import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.diagnose import DiagnosticEngine, InputError, evaluate
from scripts.profile_store import ProfileStore
from scripts.demo import replay

ROOT = Path(__file__).resolve().parent.parent


class ScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = DiagnosticEngine()

    def score(self, question, answer):
        return evaluate(self.engine.questions[question], answer, self.engine.misconceptions)

    def test_correct_scalar_vector_matrix_and_fraction(self):
        for qid, answer in [("dp_probe", "11"), ("ws_probe", "The answer is [1,6]"),
                            ("mm_probe", [[4, 6], [1, 3]]), ("as_probe", "6/2"),
                            ("sm_probe", "(0.25,0.75)")]:
            with self.subTest(question=qid):
                self.assertEqual(self.score(qid, answer)["verdict"], "correct")

    def test_wrong_answers_and_shapes(self):
        for qid, answer in [("dp_probe", 12), ("ws_probe", [1, 5]),
                            ("ws_probe", [[1, 6]]), ("mm_probe", [4, 6, 1, 3])]:
            with self.subTest(question=qid):
                self.assertEqual(self.score(qid, answer)["verdict"], "incorrect")

    def test_pattern_hypothesis(self):
        self.assertEqual(self.score("ws_probe", [4, 8])["misconception"], "unweighted_sum")
        self.assertEqual(self.score("ws_probe", [2, 4])["misconception"], "simple_average")
        self.assertEqual(self.score("ws_probe", [0, 8])["misconception"], "winner_take_all")
        self.assertIsNone(self.score("ws_probe", [99, 99])["misconception"])

    def test_unscorable_and_unsafe_inputs(self):
        for answer in ["I'm not sure", "1+2", "1/0", "[1/4,3/4]", True, None,
                       float("inf"), float("nan"), "__import__('os').system('touch /tmp/nope')",
                       {"answer": 11}, "9" * 2001, [[[[1]]]]]:
            with self.subTest(answer=str(answer)[:60]):
                self.assertEqual(self.score("dp_probe", answer)["verdict"], "unscored")

    def test_rounding_tolerance_and_no_fuzzy_grading(self):
        self.assertEqual(self.score("sm_probe", [.2500001, .7499999])["verdict"], "correct")
        self.assertEqual(self.score("sm_probe", [.24, .76])["verdict"], "incorrect")

    def test_all_patterns_are_wrong_and_known(self):
        for question in self.engine.questions.values():
            for pattern in question["patterns"]:
                result = self.score(question["id"], pattern["answer"])
                self.assertEqual(result["verdict"], "incorrect", question["id"])
                self.assertEqual(result["misconception"], pattern["misconception"], question["id"])


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = ProfileStore(self.directory.name)
        self.engine = DiagnosticEngine()

    def call(self, action, **fields):
        request = dict(action=action, **fields)
        profile = self.store.update("student", lambda p: self.engine.transition(p, request))
        return self.engine.report(profile)

    def start(self, **fields):
        return self.call("start", **fields)

    def answer(self, response, answer):
        return self.call("answer", session_id=response["session_id"], revision=response["revision"],
                         question_id=response["next"]["question_id"], answer=answer)

    def teach(self, response):
        return self.call("teach", session_id=response["session_id"], revision=response["revision"],
                         concept=response["next"]["concept"])

    def gap(self):
        response = self.start()
        self.assertEqual(response["next"]["question_id"], "ao_probe")
        response = self.answer(response, [8, 4])
        self.assertEqual(response["next"]["question_id"], "ws_probe")
        response = self.answer(response, [4, 8])
        self.assertEqual(response["next"]["question_id"], "ws_followup")
        return self.answer(response, [10, 5])

    def test_no_learning_history(self):
        profile = self.store.load("student")
        result = self.engine.report(profile)
        self.assertEqual(result["next"]["kind"], "not_started")
        self.assertEqual(result["summary"]["questions_answered"], 0)
        self.assertEqual(self.start()["next"]["question_id"], "ao_probe")

    def test_correct_answer_skips_unneeded_followup(self):
        result = self.answer(self.start(), [6, 1])
        self.assertEqual(result["next"]["question_id"], "dp_probe")
        self.assertIn("attention_output", result["summary"]["demonstrated_understanding"])

    def test_adaptive_root_cause_and_evidence_separation(self):
        result = self.gap()
        self.assertEqual(result["next"]["kind"], "intervention")
        self.assertEqual(result["next"]["concept"], "weighted_sums")
        self.assertEqual(result["diagnosis"]["status"], "likely_gap")
        self.assertEqual(result["diagnosis"]["evidence_question_ids"], ["ws_probe", "ws_followup"])
        self.assertEqual(result["diagnosis"]["confidence"], "moderate")
        self.assertTrue(result["diagnosis"]["assumptions"])
        self.assertEqual(result["diagnosis"]["misconception_hypotheses"][0]["supporting_answers"], 2)
        self.assertNotIn("transformer_attention", result["summary"]["concepts_tested"])

    def test_inconsistent_answers_require_tiebreak(self):
        response = self.answer(self.start(), [8, 4])
        response = self.answer(response, [4, 8])
        response = self.answer(response, [6, 2])
        self.assertEqual(response["next"]["question_id"], "ws_tiebreak")
        self.assertEqual(response["summary"]["lessons_delivered"], 0)
        response = self.answer(response, [5, 10])
        self.assertEqual(response["next"]["kind"], "uncertain")
        self.assertEqual(response["diagnosis"]["status"], "uncertain")
        self.assertFalse(response["diagnosis"]["assumptions"])

    def test_two_correct_after_error_resolve_conflict(self):
        response = self.start(target="weighted_sums")
        response = self.answer(response, [4, 8])
        response = self.answer(response, [6, 2])
        response = self.answer(response, [1, 8])
        self.assertEqual(response["next"]["kind"], "complete")
        self.assertIn("weighted_sums", response["summary"]["demonstrated_understanding"])
        self.assertEqual(len(response["diagnosis"]["observations"]), 3)

    def test_single_error_is_not_a_gap(self):
        response = self.answer(self.start(target="weighted_sums"), [4, 8])
        self.assertEqual(response["next"]["kind"], "question")
        self.assertEqual(response["diagnosis"]["status"], "suspected")

    def test_unparsed_answer_repeats_without_wrong_evidence(self):
        response = self.answer(self.start(), "I think you mix them somehow")
        self.assertEqual(response["next"]["question_id"], "ao_probe")
        self.assertEqual(response["feedback"]["verdict"], "unscored")
        self.assertEqual(response["diagnosis"]["observations"], [])
        response = self.answer(response, "not sure")
        self.assertEqual(response["next"]["kind"], "uncertain")
        self.assertEqual(response["summary"]["scored_answers"], 0)

    def test_intervention_fresh_reassessment_and_transfer(self):
        response = self.teach(self.gap())
        self.assertEqual(response["next"]["question_id"], "ws_reassess")
        response = self.answer(response, [2, 6])
        self.assertEqual(response["next"]["question_id"], "ws_transfer")
        self.assertEqual(response["summary"]["improvements_verified"], 0)
        response = self.answer(response, [3, 7])
        self.assertEqual(response["next"]["kind"], "complete")
        self.assertEqual(response["summary"]["improvements_verified"], 1)
        intervention = response["summary"]["recent_interventions"][0]
        self.assertEqual(intervention["reassessment"]["verdict"], "correct")
        self.assertEqual(intervention["transfer"]["verdict"], "correct")
        self.assertIn("transformer_attention", response["summary"]["untested_concepts"])

    def test_failed_reassessment_does_not_claim_improvement(self):
        response = self.answer(self.teach(self.gap()), [5, 10])
        self.assertEqual(response["next"]["kind"], "complete")
        self.assertEqual(response["summary"]["improvements_verified"], 0)
        self.assertNotIn("weighted_sums", response["summary"]["demonstrated_understanding"])
        self.assertIsNone(response["summary"]["recent_interventions"][0]["transfer"])

    def test_failed_transfer_retains_foundation_but_not_full_improvement(self):
        response = self.answer(self.teach(self.gap()), [2, 6])
        response = self.answer(response, [10, 10])
        self.assertIn("weighted_sums", response["summary"]["demonstrated_understanding"])
        self.assertEqual(response["summary"]["improvements_verified"], 0)
        self.assertIn("weighted_sums:attention_application", response["summary"]["recommended_next_concepts"])

    def test_resume_and_start_preserve_pending_turn(self):
        response = self.answer(self.start(), [8, 4])
        resumed = self.engine.report(self.store.load("student"))
        self.assertEqual(response, resumed)
        started = self.start()
        self.assertEqual(started["next"], response["next"])
        self.assertEqual(started["session_id"], response["session_id"])
        self.assertEqual(started["summary"]["questions_answered"], 1)

    def test_restart_retains_demonstrations_without_reasking_them(self):
        response = self.answer(self.start(), [6, 1])
        restarted = self.call("restart")
        self.assertNotEqual(response["session_id"], restarted["session_id"])
        self.assertEqual(restarted["next"]["question_id"], "dp_probe")
        self.assertEqual(restarted["summary"]["sessions_recorded"], 2)
        self.assertIn("attention_output", restarted["summary"]["demonstrated_understanding"])

    def test_stale_duplicate_and_wrong_question_are_rejected_without_writes(self):
        response = self.start()
        answered = self.answer(response, [6, 1])
        original = self.store.path("student").read_bytes()
        with self.assertRaises(InputError) as caught:
            self.answer(response, [6, 1])
        self.assertEqual(caught.exception.code, "stale_turn")
        with self.assertRaises(InputError):
            self.call("answer", session_id=answered["session_id"], revision=answered["revision"],
                      question_id="ws_probe", answer=[1, 6])
        self.assertEqual(original, self.store.path("student").read_bytes())

    def test_context_disconnection_failure_and_no_matches(self):
        for status in ("disconnected", "unavailable", "no_matches", "not_requested"):
            with self.subTest(status=status):
                response = self.call("restart", canvas={"status": status})
                self.assertEqual(response["canvas"]["source"], "bundled_examples")
                self.assertEqual(response["next"]["question_id"], "ao_probe")

    def test_connected_context_preserves_citation_not_secrets(self):
        response = self.start(canvas={"status": "connected", "materials": [
            {"title": "Week 6", "url": "https://canvas.example.edu/1", "token": "discard-me"}]})
        self.assertEqual(response["canvas"]["source"], "course_materials")
        self.assertEqual(response["canvas"]["materials"][0]["title"], "Week 6")
        self.assertNotIn("discard-me", self.store.path("student").read_text())

    def test_invalid_context_and_actions_do_not_save(self):
        for request in [dict(action="delete"), dict(action="start", canvas={"status": "wrong"}),
                        dict(action="start", target="calculus"),
                        dict(action="start", canvas={"status": "connected", "materials": [{"title": "x", "url": "http://example.com"}]})]:
            with self.subTest(request=request), self.assertRaises(ValueError):
                self.store.update("student", lambda p: self.engine.transition(p, request))
        self.assertFalse(self.store.path("student").exists())

    def test_intermediate_gap_requires_demonstrated_prerequisites(self):
        response = self.start(target="matrix_multiplication")
        response = self.answer(response, [[2, 0], [0, 3]])
        self.assertEqual(response["next"]["question_id"], "dp_probe")
        response = self.answer(response, 11)
        self.assertEqual(response["next"]["question_id"], "mm_followup")
        response = self.answer(response, [[2, 3], [2, 0]])
        self.assertEqual(response["next"]["kind"], "intervention")
        self.assertEqual(response["next"]["concept"], "matrix_multiplication")

    def test_pattern_routes_to_transitive_cause_before_other_branches(self):
        response = self.start()
        # Context and all earlier items are correct, then integrated attention fails.
        while response["next"].get("question_id") != "ta_probe":
            q = self.engine.questions[response["next"]["question_id"]]
            response = self.answer(response, q["expected"])
        # Simulate a new learner whose only initial probe is integrated attention.
        # Clear prior demonstrations to verify the hint beats graph traversal order.
        def clear(profile):
            profile["concepts"] = {}
            profile["session"]["evidence"] = []
            return profile
        profile = self.store.update("student", clear)
        response = self.engine.report(profile)
        response = self.answer(response, [2, 6])
        self.assertEqual(response["next"]["question_id"], "ws_probe")

    def test_resume_during_lesson_and_transfer_preserves_turn(self):
        response = self.gap()
        self.assertEqual(self.engine.report(self.store.load("student")), response)
        response = self.teach(response)
        self.assertEqual(self.engine.report(self.store.load("student")), response)
        response = self.answer(response, [2, 6])
        self.assertEqual(self.engine.report(self.store.load("student")), response)

    def test_every_concept_has_a_working_intervention_cycle(self):
        for concept in self.engine.graph.learning_order("transformer_attention"):
            with self.subTest(concept=concept):
                response = self.call("restart", target=concept)
                for _ in range(20):
                    pending = response["next"]
                    if pending["kind"] == "intervention":
                        break
                    self.assertEqual(pending["kind"], "question")
                    question = self.engine.questions[pending["question_id"]]
                    # Independent prerequisites are answered correctly; the target is wrong.
                    answer = 999 if pending["concept"] == concept else question["expected"]
                    response = self.answer(response, answer)
                else:
                    self.fail(f"No intervention reached for {concept}")
                self.assertEqual(response["next"]["concept"], concept)
                response = self.teach(response)
                reassessment_id = response["next"]["question_id"]
                response = self.answer(response, self.engine.questions[reassessment_id]["expected"])
                self.assertEqual(response["next"]["phase"], "transfer")
                transfer_id = response["next"]["question_id"]
                self.assertNotEqual(reassessment_id, transfer_id)
                response = self.answer(response, self.engine.questions[transfer_id]["expected"])
                self.assertEqual(response["summary"]["recent_interventions"][-1]["outcome"], "improvement_verified")


class CLITests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.env = dict(os.environ, SKILL_DATA_DIR=self.directory.name)

    def cli(self, request, env=None):
        return subprocess.run([sys.executable, str(ROOT / "scripts/diagnose.py")],
                              input=request if isinstance(request, str) else json.dumps(request),
                              text=True, capture_output=True, env=env or self.env)

    def test_all_three_scenarios_through_real_cli(self):
        results = [replay(s, self.directory.name) for s in "ABC"]
        self.assertEqual([r["result"]["next"]["kind"] for r in results], ["complete", "complete", "uncertain"])
        self.assertEqual([len(r["trace"]) for r in results], [8, 6, 4])

    def test_cli_invalid_json_and_nonfinite(self):
        for value in ["broken json", "[]", '{"action":"start","answer":NaN}', "x" * 16001]:
            with self.subTest(value=value[:50]):
                result = self.cli(value)
                self.assertEqual(result.returncode, 1)
                self.assertFalse(json.loads(result.stdout)["ok"])
                self.assertEqual(result.stderr, "")

    def test_missing_environment_is_explicit(self):
        env = dict(self.env)
        env.pop("SKILL_DATA_DIR")
        env.pop("HOME", None)
        result = self.cli({"action": "start"}, env)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "missing_data_dir")

    def test_missing_skill_environment_saves_and_resumes_using_persistent_home(self):
        env = dict(self.env, HOME=self.directory.name)
        env.pop("SKILL_DATA_DIR")
        started = json.loads(self.cli({"action": "start"}, env).stdout)
        self.assertTrue(started["ok"])
        self.assertEqual(started["storage"]["configuration"], "persistent_home")
        answer = self.cli({"action": "answer", "session_id": started["session_id"],
                           "revision": started["revision"], "question_id": "ao_probe",
                           "answer": "1,2"}, env)
        answered = json.loads(answer.stdout)
        self.assertTrue(answered["ok"])
        resumed = json.loads(self.cli({"action": "resume"}, env).stdout)
        self.assertEqual(resumed, answered)
        self.assertEqual(resumed["summary"]["questions_answered"], 1)
        self.assertTrue((Path(self.directory.name) / ".local/share/cubbie-knowledge-dna/profiles/student.json").exists())

    def test_storage_preflight_with_missing_environment_does_not_create_learning_history(self):
        env = dict(self.env, HOME=self.directory.name)
        env.pop("SKILL_DATA_DIR")
        result = subprocess.run([sys.executable, str(ROOT / "scripts/profile_store.py"), "check"],
                                text=True, capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, result.stdout)
        report = json.loads(result.stdout)
        self.assertTrue(report["storage"]["read_write_verified"])
        root = Path(report["storage"]["data_dir"])
        self.assertEqual(list((root / "profiles").glob("*.json")), [])

    def test_stdout_is_one_bounded_json_document(self):
        result = self.cli({"action": "start", "canvas": {"status": "connected", "materials": [
            {"title": "Attention " + "数" * 120, "url": "https://canvas.example.edu/" + "a" * 300}
            for _ in range(5)]}})
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertLessEqual(len(result.stdout.strip()), 8000)
        self.assertNotIn("expected", json.loads(result.stdout)["next"])

    def test_profiles_survive_fresh_processes(self):
        started = json.loads(self.cli({"action": "start"}).stdout)
        resumed = json.loads(self.cli({"action": "resume"}).stdout)
        self.assertEqual(started, resumed)


if __name__ == "__main__":
    unittest.main()
