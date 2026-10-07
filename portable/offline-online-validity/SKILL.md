---
name: offline-online-validity
description: >-
  Test whether offline benchmark changes predict real production outcomes by
  linking controlled benchmark interventions to online metrics, comparing
  direction and magnitude, and defining the deployment domain where the
  benchmark has external validity.
---

# Offline-online validity

## Purpose

Determine whether improving the offline benchmark predicts improvement in the
real system.

Internal benchmark quality is not enough. A benchmark becomes substantially
more useful when changes in offline metrics repeatedly correspond to changes in
production outcomes that matter.

## When to use

Use when:

- benchmark-guided changes are being deployed;
- A/B or phased production experiments exist;
- a benchmark is proposed as a release gate;
- teams claim offline improvements translate into user or operational benefit.

## Required inputs

For each intervention:

- benchmark version;
- baseline and candidate system versions;
- offline scorecard;
- production experiment design;
- online outcome metrics;
- deployment population;
- dates/window;
- known confounders.

## Procedure

### 1. Define the correspondence map

Map offline metrics to the production outcomes they are expected to predict.

Example:

```text
offline grounded recall -> addressed valid findings
offline false-positive burden -> dismissed/ignored findings
offline latency -> review completion latency
offline cost -> production inference cost
```

Do not correlate every metric with everything after the fact.

### 2. Register interventions

Treat each meaningful system change as one intervention record.

Record whether the intervention changes:

- model;
- prompt;
- context;
- tools;
- routing;
- thresholds;
- post-processing.

### 3. Measure offline deltas

For each intervention compute:

```text
Δoffline = candidate - baseline
```

Use the same benchmark contract for baseline and candidate.

### 4. Measure online deltas

Use the production experiment's appropriate estimator and uncertainty. Preserve
guardrail metrics and negative outcomes.

### 5. Compare direction first

With few interventions, directional agreement is often more honest than a
correlation coefficient.

Record:

- predicted improvement / degradation / neutral;
- observed improvement / degradation / neutral;
- whether primary trade-offs matched.

### 6. Compare magnitude when sample size supports it

Across enough independent interventions, analyze:

- correlation of offline and online deltas;
- rank correlation;
- calibration or regression slope;
- false-positive offline wins;
- false-negative offline misses.

Do not over-interpret correlation from a handful of dependent experiments.

### 7. Identify validity boundaries

Find where translation fails.

Typical boundaries:

- different user segment;
- task complexity;
- domain;
- deployment latency constraints;
- human adaptation;
- feedback loops;
- model/tool version.

### 8. Update benchmark status

Classify:

```text
UNVALIDATED
DIRECTIONALLY_VALIDATED
QUANTITATIVELY_VALIDATED
FAILED_EXTERNAL_VALIDITY
```

Always state the population/domain over which the status applies.

## Output contract

Produce an `offline-online-validity.md` report with:

- correspondence map;
- intervention table;
- offline deltas;
- online deltas;
- directional agreement rate;
- quantitative association when justified;
- mismatches and confounders;
- validity domain;
- current validation status;
- benchmark changes recommended.

## Invariants

- Offline and online metrics are linked before inspecting outcomes where possible.
- Benchmark and system versions are recorded for each intervention.
- Production guardrails remain visible.
- Correlation is not claimed from too few independent interventions.
- External validity is scoped to the observed deployment domain.
- Failed predictions are retained, not explained away and removed.

## Failure and escalation conditions

Do not claim production validity when:

- only one intervention exists;
- online metrics are unrelated to the construct;
- baseline/candidate populations differ materially;
- benchmark versions changed between arms;
- confounding system changes prevent attribution;
- only successful offline predictions were selected.

## Handoffs

Use:

- `benchmark-validity-audit` to integrate external evidence;
- `benchmark-design` if repeated offline/online mismatch indicates the construct
  or workload distribution is wrong;
- `benchmark-scorecard` to preserve comparable offline deltas.

## Compact example

Suppose an offline reviewer change predicts higher recall and more comments.
Production later shows more addressed findings but also substantially higher
comment volume. Directional correspondence supports the benchmark's recall/noise
trade-off model even if exact percentage changes differ. Repeating this across
interventions is much stronger evidence than one successful experiment.
