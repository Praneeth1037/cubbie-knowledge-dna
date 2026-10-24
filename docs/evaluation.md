# Executed synthetic evaluation

These are authored synthetic trajectories, not a validated study of real student learning. Labels describe the simulated responses. No paid model or real academic account was used.

| Policy | Correct cause / labeled cases | Mean diagnostic questions | Unsupported causal claims / all cases | Correct targeted repair / labeled cases | Uncertain cases handled | Visible revision |
| --- | --- | --- | --- | --- | --- | --- |
| Fixed questionnaire | 4/4 | 8 | 0/7 | 4/4 | 2/2 | no |
| Immediate explanation | 0/4 | 1 | 0/7 | 1/4 | 0/2 | no |
| Knowledge DNA | 4/4 | 4.571 | 0/7 | 4/4 | 2/2 | yes |

Mandatory same-initial-answer test: **PASS**. A and B both begin with `1`, then live tests distinguish response completeness from weighted aggregation.

Methods: Fixed asks the same eight diagnostic items, then uses the same conservative evidence threshold as Knowledge DNA. It can be equally accurate but asks unnecessary items. Immediate explanation reveals the initial answer and gives weighted practice; it makes no causal claim and gets no invented diagnosis credit. Knowledge DNA chooses experiments from competing categorical predictions and visibly reduces support after contrary evidence.

Four cases have a labeled cause; C and the isolated-error case require uncertainty, and D has no demonstrated gap. Scores above are counts, not statistical confidence. Unsupported means a nonempty cause without the required live evidence; all supported adaptive labels require two direct errors or the specific completeness checks.

Limitations: the tiny hand-authored corpus shares its question bank and error assumptions with the engine; it is not held out, randomized, or independently annotated. Transfer is a conservative keyword rubric. Correct post-lesson answers were authored, so this evaluation cannot establish that instruction caused learning. Lower question count is relative to the fixed baseline, not immediate explanation.

Reproduce: `python3 scripts/evaluate.py --output evaluation/results.json --markdown docs/evaluation.md`.
