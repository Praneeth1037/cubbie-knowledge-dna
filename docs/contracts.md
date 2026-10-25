# JSON contract — engine 3.0

All runtime scripts use Python 3.12 and the standard library. No HTTP calls, native-tool
clients or paid API exist. Commands run from the Skill folder. File input is preferred in
Cubbie; one JSON object on stdin is also supported. stdout contains one JSON object per call.

## Commands and request files

For each command below, create `request.json` with the example JSON. For student text use
`json.dumps` or the host's structured file-writing ability; never shell interpolation.

| Command | Minimal request file |
| --- | --- |
| `python3 scripts/diagnose.py start --input request.json` | `{"learner_id":"student","scenario":"attention"}` |
| `python3 scripts/diagnose.py answer --input request.json` | `{"session_id":"FROM_OUTPUT","revision":1,"question_id":"attention_initial","answer":"1","continuation":"FROM_OUTPUT","temporary":false}` |
| `python3 scripts/diagnose.py repair --input request.json` | `{"session_id":"FROM_OUTPUT","revision":7,"continuation":"FROM_OUTPUT"}` |
| `python3 scripts/diagnose.py report --input request.json` | `{"learner_id":"student"}` |
| `python3 scripts/diagnose.py resume --input request.json` | `{"learner_id":"student"}` |
| `python3 scripts/diagnose.py skip --input request.json` | `{"session_id":"FROM_OUTPUT","revision":1,"continuation":"FROM_OUTPUT"}` |
| `python3 scripts/diagnose.py verify --input request.json` | `{"session_id":"FROM_OUTPUT","revision":1,"continuation":"FROM_OUTPUT"}` |
| `python3 scripts/diagnose.py restart --input request.json` | `{"learner_id":"student","scenario":"attention"}` |
| `python3 scripts/diagnose.py storage-check` | No file; checks actual storage, or returns explicit temporary mode |
| `python3 scripts/diagnose.py demo` | No file; isolated synthetic students, no real records touched |
| `python3 scripts/diagnose.py --sample` | Same isolated demo, no real records touched |
| `python3 scripts/diagnose.py recover --input request.json` | `{"learner_id":"student"}`; explicitly quarantine a corrupt profile after consent |

IDs and revisions above are placeholders, never fixed turn numbers. Every answer and every
lesson acknowledgment must refer to the latest output. Learner IDs default to `student` and
must be 1–64 letters, digits, underscores or hyphens, beginning with a letter/digit.
`message_id` is optional (at most 80 characters) and deduplicates a native incoming message.

Scenarios: `writing` (simple A/B paragraph demo), `attention`, `false_mastery`, `academic_forensics`. Diagnostic question budget:
integer 3–10, default 8. A question is never repeated inside an investigation. Practice,
independent verification and transfer are separate phases outside that diagnostic budget.
`start` preserves an existing session; `restart` archives it and starts a fresh assessment.
No expiry or permanent-mastery inference is attached to old demonstrations.

Writing start/restart example: `{"learner_id":"student","scenario":"writing"}`. Its
hypotheses are writing_claim, writing_evidence, writing_link and writing_isolated. A/B
responses are scored without numerical math. Each targeted finding still requires two
distinct direct errors, and a correct check can reduce an earlier hypothesis's support.

On start/restart, `initial_exposed:true` replaces the familiar opening. Optional
`exposed_questions` contains at most 30 known IDs and excludes those items from selection.
Never relabel a previously explained response as independent. A failed independent check
before intervention returns to diagnosis in the same session; after repair, a different
unused independent item is selected. No item is repeated to manufacture improvement.

## Successful output

```json
{
  "ok": true,
  "engine": "knowledge-dna",
  "engine_version": "3.0",
  "session_id": "ACTUAL_UUID",
  "revision": 1,
  "next": {
    "kind": "question",
    "question_id": "attention_initial",
    "phase": "diagnostic",
    "concept": "attention_output",
    "prompt": "THE ACTUAL QUESTION",
    "selection": {"reason": "THE ACTUAL SELECTION REASON"}
  },
  "last_observation": null,
  "feedback": "Let's investigate with short, discriminating checks.",
  "revision_message": null,
  "hypotheses": [],
  "report": {},
  "storage": {"mode": "persistent", "saved": true},
  "continuation": "OPAQUE_CHECKPOINT",
  "execution": {"engine":"knowledge-dna","version":"3.0","command":"start","run_id":"ACTUAL_ID","observations":0,"evidence_digest":"ACTUAL_DIGEST"}
}
```

This illustrates shape, not a real execution receipt. Inspect real outputs. Receipts and
hashes aid debugging; they are not cryptographic attestations that Cubbie ran a tool.
Never make up IDs, observations, source data or receipt fields.

`next.kind` is question, intervention, complete or uncertain. An empty resume/report returns
`not_started`. An intervention includes only its targeted lesson. Pending questions do not
expose `expected` answers. `last_observation.verdict` is correct, incorrect, incomplete,
partial or unscored. Its signal names a narrower response pattern where supported.

`report` includes the original goal, observed difficulty, supported/uncertain explanation,
its evidence IDs, scoped understanding, actual repair and verification outcomes, and a
specific next step. Full `report` commands additionally include hypothesis evidence for and
against, source provenance, a bounded response path, and practice/independent/transfer
answers. Answer excerpts in a compact report are truncated; original bounded answers remain
in the profile. Anything longer belongs in a document created by Cubbie from the local data.

Understanding levels are: not demonstrated; partially demonstrated; demonstrated on
 diagnostic examples; demonstrated on independent examples; demonstrated in a new application.
These are scoped educational observations, not enduring traits. A keyword-rubric pass is
explicitly a pass on that rubric, not proof of general semantic understanding.

## Temporary mode

If writable persistent storage is unavailable, success still returns the next experiment:

```json
{"storage":{"mode":"temporary","saved":false,"error":{"code":"missing_data_dir","message":"ACTUAL ERROR"}},"continuation":"ACTUAL_TOKEN"}
```

Include the token and `"temporary":true` on **every following command**, including report
and resume. The token is bounded compressed JSON; it is neither encrypted nor authenticated.
It is a checkpoint within the student's private conversation, never an external data upload.
Do not print it in ordinary iMessages. The latest token replaces the previous token. No token
means no recoverable temporary history. Normal persistent replies also include a checkpoint
so an I/O failure between turns need not destroy the investigation. Do not silently import
client-held temporary state as verified persistent history.

A host directory takes priority. Missing `SKILL_DATA_DIR` initializes that variable from
persistent HOME inside the script. Invalid or unwritable explicit paths do not redirect to
another persistent location. Corrupt or newer-schema files remain intact, with temporary
mode available. `recover` explicitly moves bytes to a timestamped `.bak`; it never deletes
or claims to reconstruct the lost contents. The next start creates a new profile.

## Academic evidence

Optional start fields:

```json
{
  "scenario":"academic_forensics",
  "evidence_authorized":true,
  "connections":{"canvas":"connected","google":"connected"},
  "sources":[{
    "id":"feedback-1",
    "source_type":"canvas_feedback",
    "title":"Actual assignment title",
    "url":"https://canvas.example.edu/assignments/1",
    "reference":"Optional page or section",
    "excerpt":"Actual relevant excerpt, or a clearly inferred compact summary.",
    "evidence_type":"direct",
    "supports":["tensor_shapes","broadcasting"],
    "synthetic":false
  }]
}
```

This is schema documentation. Do not pretend its example values were retrieved. Connections:
connected, disconnected, unavailable, no_matches, not_requested. Real sources require both
explicit authorization and the relevant connected provider. Native Cubbie tools fetch them;
Python only validates the structured evidence. Missing accounts do not block live questions.

At most six sources. IDs ≤50 characters, titles ≤100, excerpts ≤240, references ≤120,
URLs ≤240. Each source needs a stable HTTPS URL or reference. Query parameters and fragments
are removed from links to avoid retaining signed tokens. Sources and synthetic examples
cannot be mixed. Synthetic input requires `synthetic_mode:true` and each `synthetic:true`;
outputs preserve that label and do not claim a real connection.

Attention hypotheses: incomplete_response, scalar_multiplication, vector_addition,
weighted_aggregation. Academic hypotheses: tensor_shapes, broadcasting, notation_to_code,
isolated_error. A source's `supports` is a routing hypothesis supplied by Cubbie, not a
factual conclusion. Source priors are capped at two ordinal units per hypothesis and stored
separately from live evidence. They cannot satisfy a diagnostic stopping threshold.

## Selection and stopping

Each eligible diagnostic supplies authored categorical predictions under each hypothesis.
The selector sums separated pair weights, adds tested-hypothesis coverage, and subtracts
`2 × difficulty`; hypothesis weights are `1 + max(0, ordinal support)`. Highest score wins,
then explicit priority, then stable question ID. No probabilities or information-gain claim
is made. A 100-point bonus selects the low-cost dimension experiment after an incomplete
vector. Explicit question dependencies and graph prerequisites isolate component operations
before testing their combination. Already asked items and ineligible follow-ups are excluded.

A likely operational gap requires two distinct directly targeted incorrect answers, no
correct direct counterexample, and at least four ordinal units. An incomplete-response
finding instead requires the initial incomplete reply plus successful dimension, scalar,
addition and fresh weighted checks. It does not establish the student's intent. Conflicts,
ambiguous answers, exhausted experiments or budget expiry produce uncertainty.

## Errors and retention

Failure: `{"ok":false,"error":{"code":"...","message":"..."}}` with nonzero exit status.
Stale or duplicate turns do not write. `invalid_input` asks for a corrected contract;
`continuation_required` needs the prior checkpoint or a new investigation. Persistent I/O
errors are reported inside temporary-mode storage metadata when investigation can continue.
All normal command outputs stay below 8,000 characters; diagnostic budget ≤10, ≤16 recorded
answers, and ≤512 characters per text answer bound runtime and record size. V3 retains only
the latest ten archived investigations plus the current one, with compact excerpts. Old v1
history is preserved. Learners can manage their own private data; no records ship in GitHub.
