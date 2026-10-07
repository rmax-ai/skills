---
name: novel-finding-adjudication
description: >-
  Adjudicate candidate outputs that do not match existing ground truth so valid
  novel discoveries receive credit without silently mutating fixed benchmark
  denominators. Use for open-ended discovery benchmarks with incomplete
  references.
---

# Novel finding adjudication

## Purpose

Handle the central open-set evaluation problem:

> Candidate output does not match the reference set.

That fact alone does not imply the output is false. It may be a valid discovery
that the benchmark builders missed.

This skill separates "unmatched" from "invalid."

## When to use

Use after `semantic-output-matching` when:

- reference sets are known or suspected to be incomplete;
- candidate systems can discover genuinely new findings;
- precision would otherwise penalize novel valid outputs.

## Required inputs

- unmatched candidate outputs;
- benchmark case evidence;
- frozen rubric;
- existing gold findings;
- matcher results;
- adjudicator configuration;
- policy for updating or not updating the gold set.

## Procedure

### 1. Re-check atomicity and matching

Before correctness judging, verify that the output is atomic and was not missed
because of matcher failure.

Possible outcomes:

- hidden duplicate/equivalent;
- partial match;
- genuinely unmatched.

Only the last category proceeds as novel.

### 2. Judge under the same rubric

Apply exactly the rubric used for ground-truth construction.

Do not impose a higher bar because the finding came from the candidate system.
Do not lower the bar because it is interesting.

### 3. Record evidence

For each novel output record:

```yaml
candidate_id: string
case_id: string
status: novel_valid|invalid|uncertain|duplicate
evidence: [string]
rubric_version: string
judge_version: string
```

### 4. Distinguish scoring from corpus maintenance

A novel valid finding can receive credit in an augmented precision metric
without immediately entering the frozen cross-system denominator.

This distinction matters:

- **evaluation event:** candidate deserves credit;
- **benchmark maintenance event:** future benchmark versions may add the new
  gold item after independent review.

Do not mutate the active benchmark between candidate systems.

### 5. Track benchmark incompleteness

Report:

- novel valid findings per system;
- novel-valid rate among unmatched outputs;
- categories/severities of novel findings;
- cases with repeated novel discoveries;
- whether one source class is systematically absent from the gold set.

### 6. Promote findings only between versions

If the benchmark maintains an evolving corpus:

1. independent review;
2. deduplication against full gold set;
3. provenance capture;
4. add to next benchmark version;
5. recompute fixed-reference comparisons only in the new version.

## Output contract

Produce:

- `novel-adjudications.*`;
- augmented precision inputs;
- incompleteness diagnostics;
- proposed next-version gold additions, separately from active scoring.

## Invariants

- Unmatched is not false.
- Novel outputs use the same correctness rubric as gold construction.
- Active benchmark ground truth is immutable during a comparison.
- Novel-valid credit and gold-set promotion are separate operations.
- Candidate-dependent denominators are labelled as such.
- Matcher errors are corrected before novel correctness judging.

## Failure and escalation conditions

Escalate when:

- novel-valid findings are common enough to undermine fixed-reference recall;
- adjudicators know which candidate system produced the finding and bias is a
  concern;
- novel findings cluster in high-severity cases absent from ground truth;
- gold promotion happens mid-comparison;
- the same judge both generated and adjudicates most novel findings without
  calibration.

## Handoffs

Use:

- `ground-truth-construction` to incorporate independently verified findings
  into a future benchmark version;
- `benchmark-scorecard` for grounded versus augmented metrics;
- `benchmark-validity-audit` when novel yield indicates substantial reference
  incompleteness.

## Compact example

A reviewer emits a security issue not present in the gold set. The matcher marks
it unmatched. Independent adjudication confirms it is valid. Count it as a
novel true positive in augmented precision, record it as evidence of benchmark
incompleteness, and consider adding it to the next benchmark version. Do not
retroactively change the denominator for systems already evaluated.
