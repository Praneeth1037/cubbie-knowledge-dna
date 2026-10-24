# Canvas + Google Docs forensics

Reproducible local synthetic student replay against the real Python engine. This is not a live Cubbie account transcript. Student responses are authored; selections and results are computed.

Reproduce: `python3 scripts/demo_runner.py --scenario academic --json`.

All source records below are synthetic. Neither Canvas nor Google was accessed. Real connected retrieval requires the separate live acceptance test.

**Cubbie:** A tensor has shape (2,4,8). What is its shape after swapping axes 1 and 2? Use zero-based axes.

**Student:** [2, 4, 8]

**Observation:** incorrect. That check differs from the expected result; one error does not establish its cause.

Developer selection reason: Use source-derived priors to choose a live test; the records alone do not establish a gap.

**Cubbie:** A tensor has shape (3,5,7). Swap axes 0 and 2. What is the new shape?

**Student:** [3, 5, 7]

**Observation:** incorrect. That check differs from the expected result; one error does not establish its cause.

Developer selection reason: Distinguish remaining explanations with an unasked operation check.

**Targeted repair:** tensor_shapes

Swapping axes exchanges those positions in the shape, not the values of every dimension. (2,3,4), swap axes 0 and 1: (3,2,4). Attention masks and score tensors must refer to matching axes.

**Cubbie:** Practice: shape (2,3,5), swap axes 1 and 2. What shape results?

**Student:** [2, 5, 3]

**Observation:** correct. That check is correct.

Developer selection reason: Try new values after the delivered targeted lesson.

**Cubbie:** Independent check: shape (4,6,9), swap axes 0 and 2. What shape results?

**Student:** [9, 6, 4]

**Observation:** correct. That check is correct.

Developer selection reason: Practice succeeded; now change the conditions independently.

**Cubbie:** Why track tensor dimensions when applying a mask to attention scores?

**Student:** The mask shape must align with the correct attention dimensions.

**Observation:** correct. Your explanation meets the stated rubric.

Developer selection reason: A numerical success does not establish transfer to an explanation of attention.

## Actual computed report

```json
{
  "original_goal": "Tensor implementation",
  "diagnosis": {
    "status": "supported",
    "hypothesis": "tensor_shapes",
    "basis": [
      "shape_initial",
      "shape_followup"
    ],
    "observed_pattern": "Two distinct checks of this operation were incorrect; the cause remains a likely explanation.",
    "language": "A likely explanation on these examples; not a personal trait."
  },
  "observed_difficulty": "Two distinct checks of this operation were incorrect; the cause remains a likely explanation.",
  "understanding": {
    "calculation": "demonstrated on independent examples",
    "transfer": "demonstrated in a new application"
  },
  "intervention": {
    "id": "tensor_shapes",
    "delivered": true,
    "requested_directly": false,
    "practice": "correct",
    "independent": "correct",
    "transfer": "correct"
  },
  "improvement_verified": true,
  "recall_application_mismatch": false,
  "diagnostic_questions_used": 2,
  "next_step": "Recheck tensor_shapes in a later session, then continue toward Tensor implementation."
}
```

## Preserved provenance

```json
[
  {
    "id": "synthetic-canvas-1",
    "title": "SYNTHETIC Assignment 1",
    "excerpt": "Incorrect tensor shape after reshaping.",
    "source_type": "canvas_feedback",
    "url": "https://canvas.example.invalid/assignments/1",
    "reference": "",
    "evidence_type": "direct",
    "supports": [
      "tensor_shapes",
      "notation_to_code"
    ],
    "synthetic": true
  },
  {
    "id": "synthetic-canvas-2",
    "title": "SYNTHETIC Assignment 2",
    "excerpt": "Mask applied to the wrong dimension.",
    "source_type": "canvas_feedback",
    "url": "https://canvas.example.invalid/assignments/2",
    "reference": "",
    "evidence_type": "direct",
    "supports": [
      "tensor_shapes",
      "broadcasting"
    ],
    "synthetic": true
  },
  {
    "id": "synthetic-docs-1",
    "title": "SYNTHETIC attention notes",
    "excerpt": "Scaled dot-product attention computes softmax(QK^T / sqrt(d_k)) V. This is an example note, not evidence of any real student's understanding.",
    "source_type": "google_docs",
    "url": "",
    "reference": "bundled synthetic notes, paragraph 1",
    "evidence_type": "direct",
    "supports": [
      "notation_to_code"
    ],
    "synthetic": true
  }
]
```
