# Transformer attention investigation

Reproducible local synthetic student replay against the real Python engine. This is not a live Cubbie account transcript. Student responses are authored; selections and results are computed.

Reproduce: `python3 scripts/demo_runner.py --scenario B --json`.

**Cubbie:** V1=[2,0], V2=[0,4]; attention weights are 0.75 and 0.25. What is the attention-weighted output? Reply as a two-number vector.

**Student:** 1

**Observation:** incomplete. You sent one number; the requested response contains multiple components.

Developer selection reason: Establish the initial observation without explaining the answer.

**Cubbie:** If we add two vectors that each contain two numbers, how many numbers should the result contain? Briefly say why.

**Student:** 2

**Observation:** correct. That check is correct.

**Hypothesis revision:** This correct check makes the following explanation less likely: Weights and values may be combined using the wrong operation.

Developer selection reason: Distinguish remaining explanations with an unasked operation check.

**Cubbie:** What is 0.75 × [2,0]? Reply as a vector.

**Student:** [1.5, 0]

**Observation:** correct. That check is correct.

**Hypothesis revision:** You multiplied the vector correctly. A scalar-multiplication gap is less likely; let's check combining values or reporting the result.

Developer selection reason: Distinguish remaining explanations with an unasked operation check.

**Cubbie:** What is [1.5,0] + [0,1]? Reply as a vector.

**Student:** [1.5, 1]

**Observation:** correct. That check is correct.

**Hypothesis revision:** This correct check makes the following explanation less likely: Components may not be added in matching positions.

Developer selection reason: Distinguish remaining explanations with an unasked operation check.

**Cubbie:** Weights [0.6,0.4] combine values [5,0] and [0,10]. What is the weighted sum?

**Student:** [5, 10]

**Observation:** incorrect. That response is useful evidence; let's distinguish the possible causes.

Developer selection reason: Distinguish remaining explanations with an unasked operation check.

**Cubbie:** Check another case: weights [0.2,0.8], values [10,0] and [0,5]. What is the output vector?

**Student:** [10, 5]

**Observation:** incorrect. That response is useful evidence; let's distinguish the possible causes.

Developer selection reason: Distinguish remaining explanations with an unasked operation check.

**Targeted repair:** weighted_sums

Scale each value by its own weight, then add matching components. 0.25×[8,0]+0.75×[0,4]=[2,0]+[0,3]=[2,3]. This mixes information from value vectors according to attention weights.

**Cubbie:** Practice: weights [0.5,0.5] combine [6,2] and [2,4]. Give the weighted sum.

**Student:** [4, 3]

**Observation:** correct. That check is correct.

Developer selection reason: Try new values after the delivered targeted lesson.

**Cubbie:** Independent check: V1=[4,2], V2=[0,6], weights [0.25,0.75]. What is the weighted output?

**Student:** [1, 5]

**Observation:** correct. That check is correct.

Developer selection reason: Practice succeeded; now change the conditions independently.

**Cubbie:** Why does a Transformer multiply attention weights by value vectors and add the results?

**Student:** Attention combines information from value vectors according to their weights.

**Observation:** correct. Your explanation meets the stated rubric.

Developer selection reason: A numerical success does not establish transfer to an explanation of attention.

## Same initial answer, different cause

Both A and B begin with `1`. A subsequently answers the fresh weighted check correctly and supports response completeness. B gives two direct aggregation errors and supports weighted aggregation. This distinction is a mandatory automated test.

## Actual computed report

```json
{
  "original_goal": "Transformer attention",
  "diagnosis": {
    "status": "supported",
    "hypothesis": "weighted_aggregation",
    "basis": [
      "weighted_probe",
      "weighted_followup"
    ],
    "observed_pattern": "On two weighted checks, the responses added value vectors without applying their weights.",
    "language": "A likely explanation on these examples; not a personal trait."
  },
  "observed_difficulty": "On two weighted checks, the responses added value vectors without applying their weights.",
  "understanding": {
    "calculation": "demonstrated on independent examples",
    "transfer": "demonstrated in a new application"
  },
  "intervention": {
    "id": "weighted_sums",
    "delivered": true,
    "requested_directly": false,
    "practice": "correct",
    "independent": "correct",
    "transfer": "correct"
  },
  "improvement_verified": true,
  "recall_application_mismatch": false,
  "diagnostic_questions_used": 6,
  "next_step": "Recheck weighted_sums in a later session, then continue toward Transformer attention."
}
```
