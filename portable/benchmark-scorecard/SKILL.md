---
name: benchmark-scorecard
description: >-
  Turn benchmark run artifacts into a reproducible multidimensional scorecard
  with quality, coverage, variance, failures, latency, cost, and meaningful
  slices. Use instead of reporting a single leaderboard number.
---

# Benchmark scorecard

## Purpose

Summarize benchmark performance without hiding the capability surface behind
one aggregate score.

A scorecard should support decisions, expose trade-offs, and make benchmark
uncertainty visible.

## When to use

Use after candidate runs, matching, and judging are complete.

Use it for:

- model/system comparisons;
- regression testing;
- release gates;
- architecture experiments;
- offline/online experiment comparison.

## Required inputs

- benchmark design and metric definitions;
- candidate run records;
- matched reference results;
- novel-finding adjudications where applicable;
- runtime/cost/latency data;
- failure and retry records;
- pre-registered slice labels.

## Procedure

### 1. Validate run completeness

Before scoring, account for:

- successful runs;
- timeouts;
- crashes;
- malformed outputs;
- retries;
- missing cases.

Never drop failed attempts silently.

### 2. Compute primary quality metrics

Use exactly the definitions from the benchmark contract.

For reference-based discovery tasks, distinguish fixed-reference metrics from
metrics that incorporate newly adjudicated findings.

Name them explicitly, for example:

- `grounded_precision`;
- `grounded_recall`;
- `augmented_precision`;
- `augmented_recall`.

Use fixed-reference metrics for cross-system ranking. Flag metrics whose
denominator depends on the candidate system and treat candidate-dependent
(augmented) metrics as diagnostic rather than ranking inputs.

### 3. Compute operational metrics

At minimum when available:

- end-to-end latency;
- model/tool cost;
- failure rate;
- retry rate;
- output volume/noise;
- human escalation rate.

State what latency includes and excludes.

### 4. Aggregate repeated runs

For stochastic systems report:

- mean;
- standard deviation;
- min/max or quantiles;
- confidence interval when justified;
- number of repetitions.

Do not compare a single lucky run against another system's mean.

### 5. Report slices

Produce the same core metrics by meaningful slice.

Examples:

```text
overall
├── simple / medium / complex
├── low / medium / high severity
├── short / long context
├── tool-free / tool-heavy
└── domain or language
```

Call out slices with small sample sizes.

### 6. Present trade-offs

When one system improves recall by emitting more findings, show the associated
precision, comment volume, latency, or cost change.

Use Pareto comparisons when no single system dominates.

### 7. Report uncertainty and limitations

Include:

- judge calibration status;
- matcher calibration status;
- ground-truth completeness caveat;
- contamination risk;
- unstable slices;
- metric definitions that are system-dependent.

### 8. State the decision

End with the narrowest decision supported by the data.

Example:

> System B improves grounded recall at similar precision, but the latency
> increase violates the interactive release constraint; do not deploy it in the
> synchronous path.

## Output contract

Produce:

- machine-readable `scorecard.json` or equivalent;
- human-readable `scorecard.md`;
- one comparison table for primary metrics;
- slice table(s);
- run completeness section;
- uncertainty/validity note;
- decision statement.

Recommended top-level structure:

```yaml
benchmark_version: string
system_version: string
runs: integer
quality: {}
operations: {}
stability: {}
slices: {}
validity_notes: []
decision: string
```

## Invariants

- Failed runs remain in the denominator defined by the protocol.
- Metric formulas and denominator semantics are visible.
- Mean is not reported without run count for stochastic systems.
- Aggregate results are accompanied by slices.
- Cost and latency boundaries are explicit.
- The scorecard states what decision the evidence supports.

## Failure and escalation conditions

Withhold a comparative scorecard when:

- systems were evaluated on materially different case sets;
- metric definitions changed between systems;
- run failures were selectively removed;
- judge/matcher versions differ without a sensitivity analysis;
- sample sizes are too small for claimed slice conclusions.

## Handoffs

Use:

- `benchmark-stability-test` when rankings appear fragile;
- `benchmark-validity-audit` before strong external claims;
- `offline-online-validity` when production outcomes are available.

## Compact example

Instead of "Reviewer B scores 82," report that B gains 11 points of grounded
recall at a 2-point precision loss, emits 45% more findings, costs 8% less,
fails 0.5% of runs, and gains are concentrated in high-severity correctness
issues. That description is actionable.
