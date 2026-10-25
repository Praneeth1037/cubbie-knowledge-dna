# Verification snapshot

## Local and CI checks

Python 3.12.6, October 24, 2026:

```text
----------------------------------------------------------------------
Ran 125 tests in 2.701s

OK
```

The official Skill validator passes. GitHub Actions runs Python 3.12 Linux tests, demos and
artifact-regeneration checks. The writing runtime commit `690453d` passed its 124-test CI;
the additional regression above covers the exact failed-check / fresh-check history observed
in the live test. Runtime uses the standard library, with no GPU, paid API or network calls.

## Authorized live writing test

An actual Cubbie iMessage conversation exercised the non-math writing demo with authored
synthetic answers and a separate demo learner. The installed runtime was `690453d`.

Observed behavior:

- A wrong opening choice led to investigation before teaching.
- Correct main-point and evidence checks reduced those hypotheses' support.
- Two explanation-link errors supported a targeted lesson.
- Resume returned the same pending question with two prior observations and no reset.
- A failed independent attempt was preserved; a later correction did not rewrite history.
- A different independent check and a transfer explanation then passed.
- The report showed persistent storage and a confirmed save, with nine recorded answers.

The reported evidence digest `e09c30def18d2aaa` and revision 12 matched a local replay of the
same scored responses, including the earlier failure and fresh verification. This is a
consistency check, not cryptographic remote attestation or proof of real-world learning.
The private chat transcript, recipient number and real learner data are not published.

The updated Transformer branch is covered locally, including the user-reported early-stop
regression. Real connected Canvas/Google retrieval remains unverified. Synthetic fixtures
must not be presented as connected student data. No hackathon entry has been submitted.
