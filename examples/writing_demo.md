# Simple non-math demo: investigate a paragraph

This is a local synthetic replay against the real diagnostic engine, not a claim of live iMessage execution.

Reproduce: `python3 scripts/demo_runner.py --scenario writing --json`.

**Student:** My paragraphs list facts, but my teacher says I do not explain my point. Investigate why before teaching.

**Cubbie:** A paragraph says: 'School gardens are worth funding. Students learn where food comes from.' Which ending strengthens the argument? A: This practical learning is a reason to invest in gardens. B: The garden has a green gate. Reply A or B.

**Student:** B

**Observation:** incorrect

**Cubbie:** Which sentence states a main point? A: The library opens at eight. B: Schools should keep libraries open later. Reply A or B.

**Student:** B

**Observation:** correct

**Hypothesis revision:** This correct check makes the following explanation less likely: The student may not distinguish a main point from a factual detail.

**Cubbie:** Main point: Keep the library open later. Which detail supports it? A: Many students lack a quiet evening study space. B: The library has blue chairs. Reply A or B.

**Student:** A

**Observation:** correct

**Hypothesis revision:** This correct check makes the following explanation less likely: The student may not distinguish relevant evidence from an unrelated detail.

**Cubbie:** Main point: Bike lanes make school commutes safer. Evidence: Separate lanes reduce car-bike collisions. Which sentence explains the link? A: Fewer collisions mean less risk for students cycling to school. B: There are lanes. Reply A or B.

**Student:** B

**Observation:** incorrect

**Cubbie:** Main point: Daily reading builds vocabulary. Evidence: Books introduce unfamiliar words. Which sentence explains the link? A: Some books are paperbacks. B: Meeting new words regularly helps readers learn their meanings. Reply A or B.

**Student:** A

**Observation:** incorrect

**Targeted repair:** writing_link

After giving evidence, explain why it supports your main point. Do not just add another fact. Point: More shade makes playgrounds comfortable. Evidence: Shade keeps surfaces cooler. Link: Cooler surfaces let students play without overheating.

**Cubbie:** Practice: School breakfast helps learning; hungry students struggle to concentrate. Which sentence explains why that supports the point? A: Less hunger helps students focus in lessons. B: Breakfast is sometimes hot. Reply A or B.

**Student:** A

**Observation:** correct

**Cubbie:** Fresh independent example: Refill stations reduce plastic waste; students reuse bottles instead of buying disposables. Which explains the link? A: Some stations are silver. B: Reusing bottles means fewer plastic bottles are thrown away. Reply A or B.

**Student:** B

**Observation:** correct

**Cubbie:** How would you improve a new paragraph that lists facts but does not explain its main point? Answer in one sentence.

**Student:** I would connect the evidence to the main point and explain why it supports the claim.

**Observation:** correct

## Actual computed report

```json
{
  "original_goal": "Clear paragraph arguments",
  "diagnosis": {
    "status": "supported",
    "hypothesis": "writing_link",
    "basis": [
      "writing_link_probe",
      "writing_link_followup"
    ],
    "observed_pattern": "On two checks, the selected sentence did not explain how the evidence supports the main point.",
    "language": "A likely explanation on these examples; not a personal trait."
  },
  "observed_difficulty": "On two checks, the selected sentence did not explain how the evidence supports the main point.",
  "understanding": {
    "paragraph_application": "demonstrated on independent examples",
    "transfer": "demonstrated in a new application"
  },
  "intervention": {
    "id": "writing_link",
    "delivered": true,
    "requested_directly": false,
    "practice": "correct",
    "independent": "correct",
    "transfer": "correct"
  },
  "improvement_verified": true,
  "recall_application_mismatch": false,
  "diagnostic_questions_used": 5,
  "next_step": "Recheck writing_link in a later session, then continue toward Clear paragraph arguments."
}
```
