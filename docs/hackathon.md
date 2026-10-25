# Knowledge DNA — presentation package

## 30-second pitch

“Two students can give the same wrong answer for completely different reasons. Most AI
tutors give them the same explanation. Knowledge DNA designs experiments to discover which
explanation each student actually needs. It lives in Cubbie: it can use relevant feedback
and notes with permission, test competing causes one question at a time, change its mind
when evidence disagrees, then teach a specific repair and check a new problem. The result
is an inspectable learning investigation, not another generic explanation.”

## Simple non-math demo

Use `python3 scripts/demo_runner.py --scenario writing --json` or [the writing transcript](../examples/writing_demo.md). Ask why a paragraph lists facts without making its argument clear. Reply B on the opening, B on the main-point probe (correct), A on relevant evidence (correct), then B and A on the two explanation checks (incorrect). The engine should revise away from a missing main point, teach only the evidence-to-point connection, and verify a new paragraph. Student replies are short choices; there are no calculations.

## Three-minute interactive demo

Use the actual Cubbie installation only after the real-flow test. Have a local synthetic
fallback ready and label it explicitly. Open `examples/transformer_demo.md` and the JSON
transcripts, not an invented screen or a prewritten result disguised as live execution.

| Time | Demonstration |
| --- | --- |
| 0:00–0:20 | State the same-wrong-answer problem and the initial Transformer goal. |
| 0:20–0:50 | Show the `[2,0]`, `[0,4]` weighted-output challenge. Student replies `1`. The final answer stays hidden. |
| 0:50–1:20 | Ask “Show your hypotheses.” Show incomplete reporting, scalar multiplication, vector addition and weighted aggregation as competing explanations. |
| 1:20–1:50 | Reply correctly to dimension/scalar checks. Show the scalar explanation becoming less likely. Addition succeeds; two new weighted cases fail. |
| 1:50–2:20 | Deliver the targeted scale-then-add repair; distinguish practice from independent `[1,5]` and the attention transfer explanation. |
| 2:20–2:40 | Show the report with actual answers, counterevidence, scoped verification and saved/temporary status. |
| 2:40–3:00 | If authorized accounts are available, show real relevant feedback and notes with provenance. Otherwise show the academic fixture, explicitly labeled synthetic/local. |

The two repeated weighted errors are `[5,10]` on `weighted_probe` and `[10,5]` on
`weighted_followup`. Independent answer `[1,5]` differs from the worked example `[2,3]`
and practice `[4,3]`. Do not coach the student during the independent check.

Local presenter commands:

```sh
python3 scripts/diagnose.py demo
python3 scripts/demo_runner.py --scenario B --json
python3 scripts/demo_runner.py --scenario A --json
python3 scripts/demo_runner.py --scenario academic --json
python3 scripts/demo_runner.py --scenario false_mastery --json
python3 scripts/evaluate.py --output evaluation/results.json --markdown docs/evaluation.md
```

The replay contains authored student answers, but selection, evidence updates and reports
come from the real engine. It is preparation evidence, not proof of live Cubbie execution.

## 60-second alternative

- 0:00–0:10: “Two students give the same `1`. Is that a math gap or an incomplete reply?”
- 0:10–0:25: Show A and B's identical initial answer and their shared early experiments.
- 0:25–0:40: Show scalar counterevidence, then A's successful new weighted check versus
  B's repeated aggregation errors. Different paths, different targeted help.
- 0:40–0:55: Show independent results and the side-by-side actual reports.
- 0:55–1:00: “Built as a Cubbie Skill; optional real academic evidence, no server or paid API.”

## Fallback and honesty

If account retrieval fails, continue diagnostics with no source records. If storage fails,
use the engine's explicit temporary continuation mode. If Cubbie's sandbox itself is
unavailable, use the local replay and call it a local replay. Never say a synthetic source
was a connected Canvas assignment, or that an unsaved session was persisted.

## Track 1 submission checklist

- [x] Student moment and working local investigation
- [x] Valid Agent Skills entry point; local numerical/CLI tests
- [x] Public repository already exists
- [ ] Latest 3.0 commit pushed and official validator/public-clone check passes
- [ ] Real updated Cubbie main flow, save and resume verified
- [ ] Actual Canvas/Docs retrieval verified, or clearly disclosed as not tested
- [ ] Team name and 1–4 members confirmed
- [ ] Submission account checked with official `whoami`; existing entries checked with `mine`
- [ ] Current submission window checked by the kit's live `status`
- [ ] Exact public entry preview shown and explicitly approved
- [ ] Entry submitted and public gallery result verified
- [ ] Optional public TikTok/Instagram demo posted with consent

Submit the repository URL according to the current official kit, not a fabricated gallery
link. The PDF and later kit differ on some install/submission details; confirm changing
requirements with organizers. No cutoff, video length rule, hashtag or prize criterion is
invented here. [Official kit](https://github.com/imaginix-inc/cubbie-hackathon-kit).
