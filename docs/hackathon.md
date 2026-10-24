# Hackathon presentation

## 30-second pitch

“When a student says ‘I don't understand Transformers,’ most tutors explain Transformers.
Cubbie Knowledge DNA asks what is actually missing. It follows a prerequisite graph,
checks one short question at a time, and separates a repeatable misconception from a slip.
Then it teaches the exact foundation, checks a fresh problem, and tests the connection to
attention. The student's progress survives the next text. It runs as a Cubbie Skill with
offline Python, optional Canvas context, and no server or API key.”

## Three-minute live demo

Prepare Python 3.12, this repository, a terminal, and the transcript in
`examples/demo_conversation.md`. Run the local demo before presenting. For an actual
Cubbie presentation, first complete the real-account checklist below. Do not present
the local replay as evidence of a Cubbie installation.

| Time | Show | Say |
| --- | --- | --- |
| 0:00–0:25 | Student prompt: “I want to understand Transformers.” | “The entry point is a student getting stuck, not another explanation generator.” |
| 0:25–0:45 | Root `SKILL.md` and the graph in README | “Cubbie handles conversation and Canvas. Python performs offline, inspectable checks.” |
| 0:45–1:10 | Scenario B: initial answer `[8,4]`, then `[4,8]` | “The attention error suggests weighted sums. It takes a separate math check to gather evidence.” |
| 1:10–1:30 | Follow-up answer `[10,5]`, then worked example | “Two independent foundational errors support a likely gap; the initial attention error was not enough.” |
| 1:30–1:55 | Fresh answer `[2,6]`, transfer answer `[3,7]` | “These differ from the lesson. Both checks must pass before improvement is verified.” |
| 1:55–2:15 | `python3 scripts/demo.py --scenario C --json` | “A wrong, right, wrong pattern gets a third question and ends uncertain. No invented diagnosis.” |
| 2:15–2:35 | `python3 scripts/demo.py` | “A needs no lesson. B improves through a targeted lesson. C needs more evidence.” |
| 2:35–3:00 | Saved profile, resume, public install URL | “The next text resumes the pending turn. This is an installable Skill, with no frontend, server, or paid API.” |

For terminal presentation, these commands reproduce all paths and keep demo files separate:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/demo.py
python3 scripts/demo.py --scenario B --json
python3 scripts/demo.py --scenario C --json
```

For a retained profile demonstration, select a new, dedicated directory:

```sh
python3 scripts/demo.py --scenario B --data-dir "$PWD/.local-data/presentation"
SKILL_DATA_DIR="$PWD/.local-data/presentation" python3 scripts/profile_store.py summary --learner demo_b
SKILL_DATA_DIR="$PWD/.local-data/presentation" python3 scripts/diagnose.py <<'JSON'
{"action":"resume","learner_id":"demo_b"}
JSON
```

## Real Cubbie acceptance checklist — pending

These are manual acceptance checks, not claims about tests already performed.
The first student-reported installation succeeded, but Cubbie reported unavailable
progress storage and continued with unsaved practice. This does not verify the main flow.
The recovery now initializes a missing `SKILL_DATA_DIR` from the guide's persistent HOME;
run `python3 scripts/profile_store.py check` before retesting the updated Skill.

- [ ] Publish a public GitHub repository with `SKILL.md` at its root and record the commit SHA.
- [ ] Text its URL to Cubbie; verify the Skill name, commit, and lack of extra packages/hosts/keys.
- [ ] Reply yes and verify Cubbie reports installation.
- [ ] Confirm “I don't understand Transformers” activates the Skill.
- [ ] Verify the sandbox provides `$SKILL_DATA_DIR` and saves the learning profile there.
      If the host omits it, verify `check` reports `persistent_home`, then save an answer
      and resume in a new command invocation to confirm the same pending turn and history.
- [ ] Run Scenario B from a fresh learner profile; confirm one question per text, lesson delivery,
      fresh reassessment, separate transfer and honest final progress.
- [ ] Leave a question unanswered, return later and verify the exact pending turn resumes.
- [ ] Use a fresh profile to test Scenario A and Scenario C; check that the behavior differs.
- [ ] With Canvas disconnected, verify the Skill continues using bundled examples without asking for credentials.
- [ ] With Canvas connected, verify a relevant course page/file is retrieved and cited. If no
      material matches, confirm the Skill says it is using a built-in example.
- [ ] Check iMessage readability: short messages, one question, links on their own lines.
- [ ] Verify failed reassessment/transfer does not produce an improvement claim.
- [ ] Submit the Skill URL at the tested commit; complete Track 1 within the guide's first
      10-hour window and confirm the exact cutoff with organizers.

## Guide compliance

| Supplied guide requirement | Implementation |
| --- | --- |
| Agent Skills format, publicly installable folder | Root `SKILL.md` with valid name and description; relative script commands |
| Use Cubbie's native abilities in plain words | Canvas search/read, memory, files/documents and conversation instructions |
| Scripts cannot call native abilities | JSON context passed by Cubbie; scripts have no service clients or network calls |
| Python 3.12; ephemeral Skill folder | Standard library; profiles under resolved `$SKILL_DATA_DIR`, initialized in persistent student HOME when the host omits it |
| No install commands for packages | No third-party runtime dependencies; no `cubbie.yaml` needed |
| First 8,000 output characters | Compact JSON reports; full evidence retained in profiles |
| Failure plans and text-thread UX | Canvas fallback, malformed-answer clarification, uncertainty, resume and persistence errors |
| Keep data with the student | Local private profiles; no external service or backend |
| Help learning and get consent for external actions | Fresh practice problems; no graded submissions; reminders only after time/frequency consent |
| At most 5 MiB, 300 files, 1 MiB each | Small text-only repository; generated profiles and Python caches ignored |

## Submission notes

The exact submission form, cutoff, test accounts and video rules are marked “to be confirmed”
in the supplied guide. Do not invent them. Record the tested public URL and commit, live
account results, and any remaining limitations in the final hackathon submission.
