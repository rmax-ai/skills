---
name: benchmark-stability-test
description: >-
  Stress-test whether benchmark conclusions and system rankings survive
  reasonable methodological perturbations such as reruns, judge changes,
  matcher changes, prompt variants, subsampling, and dataset perturbations.
---

# Benchmark stability test

## Purpose

Measure whether a benchmark conclusion is robust or an artifact of one specific
run, evaluator, prompt, sample, or preprocessing choice.

The object of interest is not merely score variance. It is **decision
stability**: whether the conclusion you would act on remains the same.

## When to use

Use when:

- systems have close scores;
- candidate systems or judges are stochastic;
- an LLM judge/matcher materially affects results;
- the dataset is small;
- benchmark tuning may have overfit the evaluation;
- a result will justify release, routing, or publication.

## Required inputs

- frozen benchmark version;
- candidate systems and baseline result;
- evaluator/judge configuration;
- matcher configuration;
- repeated-run capability;
- list of method choices that could reasonably vary.

## Procedure

### 1. State the baseline conclusion

Example:

> B ranks above A on grounded recall without reducing precision beyond the
> release threshold.

A stability test without a decision statement degenerates into variance
reporting.

### 2. Enumerate perturbation families

Choose perturbations that represent legitimate uncertainty, not arbitrary
sabotage.

Recommended families:

- stochastic seeds/repeated candidate runs;
- judge reruns;
- alternative calibrated judge;
- alternative calibrated matcher;
- prompt wording variants that preserve rubric meaning;
- bootstrap/subsampling;
- case removal/addition;
- slice reweighting toward the target workload;
- threshold changes within a predeclared plausible range.

### 3. Run one-factor tests first

Vary one methodological component at a time. This identifies which layer
controls the conclusion.

### 4. Run selected combined perturbations

Combine plausible changes after single-factor sensitivity is understood.

### 5. Measure stability

Report:

- score distribution;
- rank reversal frequency;
- decision reversal frequency;
- confidence interval where appropriate;
- per-slice reversal frequency;
- sensitivity to each perturbation family.

For two systems, a useful statistic is:

```text
P(B > A | allowed perturbations)
```

Treat this as a descriptive robustness measure unless the perturbation sampling
has a formal probabilistic interpretation.

### 6. Diagnose instability

Classify dominant instability source:

- candidate stochasticity;
- judge uncertainty;
- matcher uncertainty;
- sample composition;
- metric threshold;
- interaction effect.

### 7. Define the robust conclusion

Downgrade claims when required.

Example:

Instead of "B is better than A," use:

> B usually improves recall, but the ranking reverses under an alternative
> calibrated matcher; the result is not yet robust enough for a release gate.

## Output contract

Produce a stability report containing:

- baseline result and decision;
- perturbation matrix;
- run counts;
- score/ranking distributions;
- decision reversal rates;
- sensitivity by slice;
- dominant instability sources;
- robust conclusion;
- required follow-up.

## Invariants

- Perturbations preserve the benchmark's intended construct.
- Candidate and evaluator stochasticity are measured separately.
- Rank stability and score stability are both reported.
- Close aggregate scores trigger slice-level analysis.
- Failed perturbation runs remain visible.
- Post-hoc perturbations are labelled as exploratory.

## Failure and escalation conditions

Do not claim robustness when:

- too few repetitions were run to observe known stochastic variance;
- alternative judges/matchers are uncalibrated;
- only favorable perturbations are reported;
- system ranking flips frequently under reasonable choices;
- stability depends on excluding a consequential slice.

## Handoffs

Use:

- `llm-judge-calibration` when judge variance dominates;
- `semantic-output-matching` when matcher ambiguity dominates;
- `benchmark-design` when sample weighting is the main problem;
- `benchmark-validity-audit` to integrate stability into overall trust.

## Compact example

Systems A and B differ by one recall point. Across 20 reruns B wins 12 times.
With an alternative calibrated matcher A wins 14 of 20. The correct result is
"indistinguishable under current benchmark uncertainty," not a leaderboard win
for B.
