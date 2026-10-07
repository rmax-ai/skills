---
name: benchmark-validity-audit
description: >-
  Audit whether an evaluation benchmark deserves to be trusted by examining
  construct validity, sampling, ground truth, matcher and judge reliability,
  contamination, metric gaming, stability, and external validity. Use before
  making strong claims from benchmark scores.
---

# Benchmark validity audit

## Purpose

Evaluate the benchmark itself as a measurement instrument.

This skill does not ask "which system scored higher?" It asks:

> What conclusions is this benchmark actually capable of supporting?

## When to use

Use this skill for:

- adopting a third-party benchmark;
- publishing benchmark results;
- using an eval as a release gate;
- comparing benchmark versions;
- investigating suspicious leaderboard gains;
- deciding whether offline results are representative of production.

## Required inputs

Gather as much as exists:

- benchmark design/specification;
- dataset construction methodology;
- case distribution;
- rubric;
- ground-truth process;
- matcher and judge implementations;
- calibration evidence;
- metric definitions;
- candidate run protocol;
- contamination controls;
- repeated-run data;
- production correlation evidence.

Missing evidence is itself an audit finding.

## Procedure

### 1. Construct validity

Ask:

- Is the real capability explicitly defined?
- Do the tasks and metrics measure that capability rather than a convenient proxy?
- Are important failure costs represented?

### 2. Sampling validity

Ask:

- What population is claimed?
- How were cases sampled?
- Which dimensions were matched, stratified, or oversampled?
- Are convenience or survivorship biases likely?

### 3. Ground-truth validity

Ask:

- Which sources discovered reference items?
- Were heterogeneous sources used?
- Was one common rubric applied?
- How was semantic deduplication handled?
- Is residual incompleteness measured?

### 4. Matcher validity

Ask:

- Is equivalence separate from correctness?
- Has matching been calibrated against humans?
- How are partial, uncertain, duplicate, and many-to-many cases handled?

### 5. Judge validity

Ask:

- Is the automated judge calibrated against independent human labels?
- Are confusion matrices and slice disagreements reported?
- Does judge configuration overlap with candidate systems in a way that creates
  systematic preference?

### 6. Metric validity

Inspect:

- numerator and denominator;
- treatment of failures/retries;
- candidate-dependent denominators;
- incentives for verbosity or abstention;
- sensitivity to class imbalance;
- whether the ranking metric matches the operational decision.

### 7. Stability

Ask whether conclusions survive:

- reruns/seeds;
- alternative judge;
- alternative matcher;
- prompt perturbation;
- subsampling;
- small dataset changes.

### 8. Contamination and gaming

Assess:

- public exposure of cases/labels;
- likely training contamination;
- benchmark-specific prompt tuning;
- memorization opportunities;
- hidden/private holdout availability.

### 9. External validity

Ask:

- Has benchmark movement predicted production movement?
- Are real users, tasks, constraints, and error costs similar?
- Which deployment settings fall outside the benchmark?

## Rating scale

Use evidence-qualified ratings:

```text
HIGH       strong direct evidence
MEDIUM     partial evidence or limited validation
LOW        material weakness
UNKNOWN    evidence unavailable
```

Do not convert these ratings into a pseudo-precise overall number by default.

## Output contract

Produce a `benchmark-validity-audit.md` with:

```text
Construct validity
Sampling validity
Ground-truth validity
Matcher validity
Judge validity
Metric validity
Stability
Contamination/gaming
External validity
```

For each dimension include:

- rating;
- evidence;
- risk;
- recommended remediation;
- claim limitation.

Finish with:

1. `Safe claims`;
2. `Unsafe or unsupported claims`;
3. `Highest-leverage validation work`.

## Invariants

- Missing evidence becomes `UNKNOWN`, not assumed good.
- Benchmark popularity is not validity evidence.
- High judge agreement does not prove sampling validity.
- High internal consistency does not prove production validity.
- Public benchmarks explicitly assess contamination risk.
- Audit conclusions distinguish benchmark defects from candidate defects.

## Failure and escalation conditions

Escalate before high-stakes use when:

- construct or sampling validity is LOW/UNKNOWN;
- judge error is high on consequential slices;
- reference incompleteness materially changes rankings;
- a public benchmark is likely contaminated and no fresh holdout exists;
- external validity is claimed without evidence.

## Handoffs

Use:

- `llm-judge-calibration` for weak judge evidence;
- `benchmark-stability-test` for fragile rankings;
- `offline-online-validity` for external validation;
- `benchmark-design` when the benchmark requires redesign rather than patching.

## Compact example

A public code-review benchmark can have excellent human agreement and still
have MEDIUM sampling validity, HIGH contamination risk, and UNKNOWN production
validity. The correct conclusion is not "the benchmark is bad"; it is that
leaderboard claims should be narrower than claims about production reviewer
quality.
