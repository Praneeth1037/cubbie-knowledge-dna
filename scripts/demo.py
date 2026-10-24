"""Replay three real CLI flows; optional persistence in a chosen demo directory."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def replay(scenario, data_dir):
    learner = "demo_" + scenario.lower()
    env = dict(os.environ, SKILL_DATA_DIR=str(Path(data_dir).resolve()))
    bank = {q["id"]: q for q in json.loads((ROOT / "data/diagnostic_questions.json").read_text())["questions"]}

    def call(request):
        request["learner_id"] = learner
        result = subprocess.run([sys.executable, str(ROOT / "scripts/legacy_diagnose.py")],
                                input=json.dumps(request), text=True, capture_output=True,
                                env=env, cwd=ROOT, check=True)
        response = json.loads(result.stdout)
        assert response["ok"], response
        return response

    response = call({"action": "restart", "target": "transformer_attention",
                     "canvas": {"status": "disconnected"}})
    trace = []
    overrides = {
        "B": {"ao_probe": [8, 4], "ws_probe": [4, 8], "ws_followup": [10, 5]},
        "C": {"ao_probe": [8, 4], "ws_probe": [4, 8], "ws_followup": [6, 2], "ws_tiebreak": [5, 10]},
    }.get(scenario, {})
    for _ in range(30):
        pending = response["next"]
        turn = {"session_id": response["session_id"], "revision": response["revision"]}
        if pending["kind"] == "question":
            qid = pending["question_id"]
            answer = overrides.get(qid, bank[qid]["expected"])
            trace.append({"question_id": qid, "prompt": pending["prompt"], "answer": answer})
            response = call(dict(turn, action="answer", question_id=qid, answer=answer))
            trace[-1]["feedback"] = response["feedback"]
        elif pending["kind"] == "intervention":
            trace.append({"intervention": pending["concept"], "lesson": pending["lesson"]})
            response = call(dict(turn, action="teach", concept=pending["concept"]))
        else:
            break
    else:
        raise AssertionError("Demo did not terminate")
    if scenario == "A":
        assert response["next"]["kind"] == "complete"
        assert len(response["summary"]["demonstrated_understanding"]) == 8
        assert not response["summary"]["lessons_delivered"]
    elif scenario == "B":
        assert response["summary"]["improvements_verified"] >= 1
        assert response["summary"]["recent_interventions"][-1]["concept"] == "weighted_sums"
    else:
        assert response["next"]["kind"] == "uncertain"
        assert "weighted_sums" in response["summary"]["uncertain_knowledge_gaps"]
        assert not response["summary"]["lessons_delivered"]
    return {"scenario": scenario, "trace": trace, "result": response}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["A", "B", "C", "all"], default="all")
    parser.add_argument("--data-dir", help="Optional dedicated directory for saved demo profiles")
    parser.add_argument("--json", action="store_true", help="Full replay including answers, for presenters only")
    args = parser.parse_args()

    def run(directory):
        results = [replay(s, directory) for s in (["A", "B", "C"] if args.scenario == "all" else [args.scenario])]
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for result in results:
                summary = result["result"]["summary"]
                print(f"Scenario {result['scenario']}: {result['result']['next']['kind']}; "
                      f"{len(result['trace'])} turns; "
                      f"{summary['improvements_verified']} verified improvement(s)")

    if args.data_dir:
        run(args.data_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="knowledge-dna-demo-") as directory:
            run(directory)


if __name__ == "__main__":
    main()
