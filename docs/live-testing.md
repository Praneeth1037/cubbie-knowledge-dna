# Real Cubbie acceptance tests

The simple writing demo at runtime commit `690453d` was exercised through an authorized
real iMessage conversation, using built-in examples, scripted answers and a separate demo
learner. It narrowed the hypotheses, taught the supported skill, resumed the same pending
question, preserved an earlier failed check, then passed a different independent item and
transfer. The final reported digest matched a local replay of all nine recorded answers.
This is a live integration check using synthetic inputs, not a study of student learning.
No private chat transcript, contact number or real academic record is published here.

The Transformer and connected-source checks below still require live acceptance testing.

A local replay verifies Python behavior, not Cubbie's native tool execution, account access
or deployment. The earlier installed version fell back to unsaved tutoring. Do not call the
3.0 entry finished until the actual updated Skill completes this checklist on a real account.

1. Text the branch link, then approve Cubbie's fetch/update summary:
   https://github.com/Praneeth1037/cubbie-knowledge-dna/tree/main
2. In a new message: “Start Knowledge DNA. I keep getting attention calculations wrong.
   Don't teach me immediately. Run the Python investigation.”
3. Confirm that Cubbie actually runs `scripts/diagnose.py storage-check` and `start`, using
   available sandbox execution, rather than merely saying it ran them. Ask for the actual
   engine version, session ID, observation count and storage mode if debugging is needed.
   These values must be copied from real tool output. A text receipt alone is not proof.
4. Its first challenge must use `[2,0]`, `[0,4]`, weights `0.75`, `0.25`. Reply `1`.
   It should treat that as incomplete, **withhold the final vector**, and ask about dimensions.
5. Reply `2, because matching positions add`. Then answer the scalar check `[1.5,0]`.
   Confirm a scalar-multiplication gap becomes less likely. “Show your investigation” should
   cite that actual answer as counterevidence, not a confidence percentage.
6. Answer addition `[1.5,1]`. For the new weighted case answer `[5,10]`, then `[10,5]`.
   It should support weighted aggregation from those two distinct direct errors and teach
   only scale-then-add. It must not claim the first `1` proved that cause.
7. Practice `[4,3]`; independent problem `[1,5]`; transfer: “Attention combines information
   from value vectors according to their weights.” Confirm all three are recorded separately.
8. “Show my Knowledge DNA.” Check the actual report's source of difficulty, for/against
   evidence, lesson, independent answer, transfer and targeted next step. Improvement must
   be qualified to these items. Failed independent or partial transfer must not get a success claim.
9. Before answering a pending question in another session, leave and resume. Confirm the
   exact pending question and previous observation count return, without replaying answers.
10. Test a missing-storage environment only in a dedicated sandbox/test learner. It should
    continue with the same diagnostic engine in temporary mode, say progress is not saved,
    and carry the token between commands. Never damage a real profile to demonstrate failure.
11. Test Canvas and Google disconnected: the diagnostic still works and no source is invented.
12. With the student's permission and an actual connection, retrieve relevant feedback and
    notes using native abilities. Confirm real titles, excerpts/summary type, links/references
    and hypotheses in the report. Inaccessible drafts/revisions must be omitted. A source
    priority must change after contrary live evidence; sources alone cannot establish a gap.
13. If connected sources are unavailable, use `demo_runner.py --scenario academic --json`
    as a clearly labeled **local synthetic fallback**, never as a real connected demonstration.
14. Retest the A, C, D and false-mastery branches from the checked-in demo transcripts. A
    should not receive a weighted-sum misconception label; C should stay uncertain; D needs
    no repair; Q/K/V recall alone must not be called application understanding.

Record the commit tested, actual Cubbie results and any remaining failure. If execution fails,
obtain the exact command's JSON error, source folder and whether a sandbox tool was available.
Do not diagnose an absent environment variable from a conversational paraphrase alone.
Update the repository, text the branch link again, and repeat the failed rows.

The checked-in unittest suite does not access a real Cubbie account; the developer-side
Messages integration test above was separate and explicitly authorized. No Canvas or Google account was used
for the checked-in synthetic material. Submission and external social posts require a
reviewable preview and explicit approval; the official form goes public immediately.
