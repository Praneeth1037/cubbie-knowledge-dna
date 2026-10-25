# Verification matrix

The supplied guide was read before changes; the current official kit was also inspected.
Their differences are noted in `audit.md`. There are no extra packages, network hosts,
secrets, MCP servers or background services. Runtime is standard-library Python 3.12.
`SKILL.md` stays at the root and names native abilities in plain words. The existing Skill
name is preserved so an installed copy can update.

| Requirement | Evidence |
| --- | --- |
| Four cooperating engines | evidence_engine, hypothesis_engine/selector, investigation repair, independent/transfer plus profile_store |
| Numerical, incorrect, incomplete and ambiguous answers | test_answer_evaluator.py; original 56 v1 regression tests retained |
| Competing hypotheses and adaptive experiments | test_hypothesis_engine.py, test_question_selector.py |
| Same wrong answer, different causes | mandatory A/B test and executed evaluation assertion |
| Counterevidence and hypothesis revision | scalar correct check reduces ordinal support; revision message tested |
| Stable IDs, no repeats, budget stopping | test_question_selector.py and bounded state validation |
| Targeted intervention | weighted, scalar, addition, format and tensor repairs; no chapter lecture |
| Independent numerical check and separate transfer | test_hypothesis_engine.py, test_evaluation.py; `[1,5]` verification |
| Recall versus application | false_mastery replay and test; separate understanding fields |
| Session ID, revision, duplicate guards | test_end_to_end.py; old atomic-store regression checks |
| Persistence and simulated restart | actual fresh-process command tests, HOME fallback and checkpoints |
| Corrupt files and recoverable writes | preserved originals, explicit quarantine, temporary diagnostic continuation |
| Missing SKILL_DATA_DIR / both persistent locations | fresh-process tests; initialization or honest temporary mode |
| Missing Canvas / Google | test_evidence_engine.py; no invented source |
| Source provenance, authorization and synthetic labels | source validation, per-source prior IDs and real/synthetic separation |
| Machine-readable commands and file input | test_end_to_end.py, including closed interactive stdin |
| Resource bounds | 3–10 diagnostic budget, ≤16 observations, bounded answers/excerpts, compressed-state bound, <8,000-character JSON results checked by CLI tests |
| Conservative understanding and no fake confidence | enumerated levels, ordinal scores, no probabilities; independent failures/partial transfer cannot verify improvement |
| Reproducible evaluation | evaluate.py recomputes policies; synthetic limitations disclosed; snapshots reproduce exactly |
| Short iMessage UX and privacy | SKILL.md instructions, consent before records/actions, native documents for long reports |
| Public installable folder | existing GitHub repository; official validator and anonymous clone/link check required after final push |
| Real execution on Cubbie | **Writing demo observed live** using scripted synthetic replies, save/resume and a matching replay digest; Transformer live checks remain pending |
| Connected Canvas + Google execution | **Not tested on a real account**; synthetic examples are explicitly labeled |
| Hackathon submission | **Not submitted**; requires team/account details and approval of public preview |

The locally available PDF specifies 1 CPU, 2 GB RAM and a default two-minute command budget.
The implementation has no GPU/model dependency, bounded loops and small JSON data files;
local execution measurements are recorded separately from any unverified Cubbie runtime claim.
The source remains within the PDF's 300-file/5-MiB/1-MiB-per-file budgets even though the
newer kit says those historical limits do not apply. No dependency manifest is required.
