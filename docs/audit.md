# Knowledge DNA 3.0 audit

The existing graph, atomic profile store, 40-item question bank and 56 regression tests
were inspected before changes. The supplied October 19 PDF was read from Downloads.
The original implementation is retained as `scripts/legacy_diagnose.py` and its regression
tests keep their assertions, explicitly targeting that compatibility interface.

Reproduced locally before implementation:

- For expected vector `[1.5,1]`, response `"1"` was scored `incorrect`, losing the distinction
  between an incomplete answer and a mathematical error.
- Without both persistent environment variables, `ProfileStore` raised `missing_data_dir`;
  the old conversation could not continue through the engine.
- Follow-ups used graph traversal and bank order; there was no competing prediction model,
  active experiment score, source excerpt provenance, or explicit hypothesis reversal.
- The user-reported Cubbie transcript revealed the answer before investigating. This is
  evidence about the old live interaction, not proof that its Python scripts executed.
- Canvas context retained titles/links only. Google Docs evidence was absent.

The 3.0 interface adds an execution receipt, explicit save status, and a bounded temporary
continuation token when disk storage fails. It retains the existing store's atomic writes,
locking, safe learner IDs and preservation of corrupt files. No user records are stored in
the repository. Actual Cubbie tool execution and connected-account access remain manual
acceptance checks; local simulations cannot prove those integrations work on a real account.

The newer official kit differs from the PDF about package setup, installation updates and
submission links. This project needs no packages, network, secrets or backend, so the package
difference does not affect runtime. It supports both host data directories and persistent
HOME initialization. Confirm current submission windows with the official live status
command; submit the repository URL according to the current kit. Do not infer a cutoff.
