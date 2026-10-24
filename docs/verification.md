# Local verification snapshot

Run on October 24, 2026 using 3.12.6.

```text
----------------------------------------------------------------------
Ran 113 tests in 2.230s

OK
```

The official Cubbie Skill validator also passes. Nine isolated local replays completed in a measured 0.056 seconds with 21.53 MiB peak process RSS on the development Mac. These are local measurements, not a benchmark of Cubbie network latency or its runtime. Runtime code uses no GPU, network or paid API.

The same-initial-answer test passes, generated transcripts reproduce exactly, and actual evaluation details are in `evaluation/results.json`. GitHub Actions independently runs Python 3.12 Linux tests, demos and artifact-regeneration checks after publication.

The updated 3.0 flow and connected account retrieval still require real Cubbie testing. Earlier installation alone does not verify them.
