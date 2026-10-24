# Recall versus application

Reproducible local synthetic student replay against the real Python engine. This is not a live Cubbie account transcript. Student responses are authored; selections and results are computed.

Reproduce: `python3 scripts/demo_runner.py --scenario false_mastery --json`.

**Cubbie:** What are Q, K and V in attention? Give each role briefly.

**Student:** Queries describe what information a token is looking for; keys are compared for a match; values contribute content.

**Observation:** correct. Definitions are recall evidence. Next we will check application.

Developer selection reason: Establish the initial observation without explaining the answer.

**Cubbie:** V1=[2,0], V2=[0,4]; attention weights are 0.75 and 0.25. What is the attention-weighted output? Reply as a two-number vector.

**Student:** 1

**Observation:** incomplete. Your definitions worked; application has not yet been demonstrated. Let's test the operations.

Developer selection reason: Recall does not establish calculation ability.

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

**Student:** [3, 4]

**Observation:** correct. That check is correct.

**Hypothesis revision:** This correct check makes the following explanation less likely: Weights and values may be combined using the wrong operation.

Developer selection reason: Distinguish remaining explanations with an unasked operation check.

**Targeted repair:** response_format

The tested operations worked. The initial reply contained one component, so practice reporting the full vector. This does not establish why you omitted a component. A vector whose first component is 2 and second is 3 is written [2,3]. An attention output contains every component of the mixed value vectors.

**Cubbie:** Practice reporting: first component is 4, second is 3. Give the full vector.

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

## Actual computed report

```json
{
  "original_goal": "Transformer attention",
  "diagnosis": {
    "status": "supported",
    "hypothesis": "incomplete_response",
    "basis": [
      "attention_initial",
      "dimension",
      "scalar_probe",
      "addition_probe",
      "weighted_probe"
    ],
    "language": "The original response was incomplete; tested operations subsequently worked. Intent is unknown."
  },
  "observed_difficulty": "Incomplete response or component reporting; intent is not established.",
  "understanding": {
    "verbal_recall": "demonstrated on diagnostic examples",
    "calculation": "demonstrated on independent examples",
    "transfer": "demonstrated in a new application"
  },
  "intervention": {
    "id": "response_format",
    "delivered": true,
    "requested_directly": false,
    "practice": "correct",
    "independent": "correct",
    "transfer": "correct"
  },
  "improvement_verified": true,
  "recall_application_mismatch": true,
  "diagnostic_questions_used": 5,
  "next_step": "Recheck response_format in a later session, then continue toward Transformer attention."
}
```
