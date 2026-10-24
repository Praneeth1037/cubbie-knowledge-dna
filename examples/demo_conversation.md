> Legacy v1 transcript. For the 3.0 active investigation see [transformer_demo.md](transformer_demo.md).

# Three Transformer conversations

These are example student-facing transcripts of the executable demo paths. Tool names and
IDs in the notes help presenters reproduce them; Cubbie does not include those details in
student texts. Each scenario begins with a fresh profile and disconnected Canvas.

Run `python3 scripts/demo.py --json` to inspect the actual CLI replay, including recorded
verdicts and final summaries. These examples demonstrate local behavior, not a verified
installation in Cubbie.

## Scenario A: the foundations are demonstrated

**Student:** I want to understand Transformers.

**Cubbie:** Let's check the foundations first. We can use a built-in example.

**Cubbie:** A query has attention weights [0.75,0.25] and values [8,0] and [0,4]. What is its output vector?

**Student:** [6,1]

**Cubbie:** Correct. What is [1,2] dot [3,4]? Reply with one number.

**Student:** 11

**Cubbie:** Correct. Multiply [[1,2],[0,1]] by [[2,0],[1,3]]. Reply with a 2x2 matrix.

**Student:** [[4,6],[1,3]]

**Cubbie:** Correct. Softmax scores [0,ln(3)] have exponentials [1,3]. What are the normalized weights? Reply [a,b].

**Student:** [0.25,0.75]

**Cubbie:** Correct. Weights [0.25,0.75] combine vectors [4,0] and [0,8]. What is the weighted sum?

**Student:** [1,6]

**Cubbie:** Correct. Query [2,0,0,0] and key [3,1,0,0] have d_k=4. What is (q dot k)/sqrt(d_k)?

**Student:** 3

**Cubbie:** Correct. A row of attention scores is [0,0]. Their exponentials are [1,1]. What are its attention weights?

**Student:** [0.5,0.5]

**Cubbie:** Correct. Scaled query-key scores are [0,0], so exponentials are [1,1]. Values are [2,0] and [0,6]. Apply softmax then mix values. What is the output?

**Student:** [1,3]

**Cubbie:** You demonstrated the bundled foundations and attention pipeline on these checks. I didn't find a gap to remediate. This is practice evidence, not a mastery claim. Next we can explore multi-head attention. Your progress is saved.

Presenter notes: question order is `ao_probe → dp_probe → mm_probe → sm_probe → ws_probe →
as_probe → aw_probe → ta_probe`. Eight answers, no intervention, all eight concepts have
limited demonstrations. No measured improvement is claimed because there was no intervention.

## Scenario B: a weighted-sum gap, a lesson, and verified improvement

**Student:** I want to understand Transformers, but attention confuses me.

**Cubbie:** Let's check the foundations first. We can use a built-in example.

**Cubbie:** A query has attention weights [0.75,0.25] and values [8,0] and [0,4]. What is its output vector?

**Student:** [8,4]

**Cubbie:** That result suggests a possible pattern; let's check it with a different example.

**Cubbie:** Weights [0.25,0.75] combine vectors [4,0] and [0,8]. What is the weighted sum?

**Student:** [4,8]

**Cubbie:** A second check: weights [0.6,0.4] combine [10,0] and [0,5]. What is the result?

**Student:** [10,5]

**Cubbie:** Weighted sums look like the likely gap. In both foundation checks, your result added the vectors without applying the weights. That could be a concept gap or a repeated slip; we'll test it after a short example.

**Cubbie:** Multiply every coordinate of each vector by its weight, then add coordinate by coordinate.

**Cubbie:** With weights [0.25,0.75] and vectors [8,0], [0,4]:
0.25×[8,0] + 0.75×[0,4] = [2,0]+[0,3] = [2,3].

**Cubbie:** Attention does this to value vectors using attention weights. It mixes values rather than just choosing one.

**Cubbie:** Fresh check: weights [0.4,0.6] combine [5,0] and [0,10]. What is the weighted sum?

**Student:** [2,6]

**Cubbie:** Correct. Attention weights are [0.3,0.7]; value vectors are [10,0] and [0,10]. What output vector does this query receive?

**Student:** [3,7]

**Cubbie:** You passed the fresh weighted-sum check and its attention application. That verifies improvement on these items. Other foundations remain untested; we can check those next time. Your progress is saved.

Presenter notes: `ao_probe → ws_probe → ws_followup → weighted_sums lesson → ws_reassess →
ws_transfer`. The lesson uses [2,3], the reassessment [2,6], and transfer [3,7]: different
problems. The profile records two foundational error observations, an error-pattern
hypothesis, lesson delivery, and both successful fresh outcomes. It does not claim that
all of Transformer attention is mastered. Restarting preserves the weighted-sum demonstration.

## Scenario C: inconsistent evidence needs another question

**Student:** I want to understand Transformers.

**Cubbie:** We can use a built-in example. A query has attention weights [0.75,0.25] and values [8,0] and [0,4]. What is its output vector?

**Student:** [8,4]

**Cubbie:** Let's check the operation underneath that. Weights [0.25,0.75] combine vectors [4,0] and [0,8]. What is the weighted sum?

**Student:** [4,8]

**Cubbie:** A second check: weights [0.6,0.4] combine [10,0] and [0,5]. What is the result?

**Student:** [6,2]

**Cubbie:** That calculation is correct. One more check: weights [0.2,0.8] combine [5,0] and [0,10]. What is the result?

**Student:** [5,10]

**Cubbie:** Your foundation answers were mixed: one correct and two incorrect. I can't confidently declare a weighted-sum gap from that. We can talk through your steps or try again later. I've saved the uncertainty with the answers.

Presenter notes: `ao_probe → ws_probe → ws_followup → ws_tiebreak → uncertain`. The
third question is essential: the correct second answer prevents an immediate gap diagnosis.
No intervention is recorded and no improvement is claimed. The profile recommends further
practice without converting the error pattern into a confirmed misconception.

## Pause, resume, and failure examples

**Student:** Can we stop here?

**Cubbie:** Yes. Your next question and progress are saved.

**Student, later:** Resume Knowledge DNA.

**Cubbie:** Welcome back. [Repeats the exact pending question returned by `resume`.]

If the student writes “I don't know” instead of a number, the engine returns `unscored`
and keeps the question pending. A second unscorable reply ends uncertain; neither reply is
recorded as a wrong mathematical answer. If the fresh reassessment fails, no improvement
is claimed. If transfer fails after reassessment passes, the foundation demonstration
remains, with attention application recommended for practice.

If saving fails, Cubbie reports the persistence problem and does not say progress was saved.
If a course source is available, Cubbie retrieves and cites its real title and link; it
never invents a Canvas citation for these bundled examples.
