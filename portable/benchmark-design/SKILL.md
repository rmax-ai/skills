---
name: benchmark-design
description: >-
  Design an evaluation benchmark from a real-world capability claim by defining
  the construct, target task distribution, benchmark cases, slices, metrics,
  validity threats, and versioned evaluation contract. Use before collecting
  data or comparing systems.
---

# Benchmark design

## Purpose

Turn a vague evaluation question into a falsifiable benchmark specification.
The benchmark must state what real-world capability it is intended to predict,
which task population it represents, what evidence counts, and which conclusions
the resulting metrics do and do not support.

This skill designs the benchmark. It does not create ground truth, write the
final scoring rubric, or judge candidate outputs.

## When to use

Use this skill when:

- a team proposes a new benchmark or leaderboard;
- an existing eval has accumulated examples without a documented construct;
- two systems are being compared but the target workload is unclear;
- an offline metric is being treated as a proxy for production behavior.

Do not start by choosing a metric. Start by defining the capability.

## Required inputs

Collect, or explicitly mark as unknown:

- `capability_claim`: the real-world behavior the benchmark should predict;
- `target_population`: the tasks, users, repositories, workflows, or cases of interest;
- `decision`: what choice the benchmark is meant to inform;
- `constraints`: cost, latency, safety, policy, tooling, and runtime boundaries;
- `available_evidence`: production traces, historical cases, synthetic cases, labels;
- `candidate_systems`: only when comparison requirements affect benchmark design.

## Procedure

### 1. Write the construct statement

Use the form:

> Given `<task population>`, does `<system>` produce `<desired outcome>` under
> `<constraints>` with acceptable `<failure burden>`?

Decompose the construct into dimensions. Typical dimensions are correctness,
coverage, false-positive burden, severity, completeness, cost, latency,
reliability, intervention rate, and policy compliance.

Separate primary dimensions from diagnostics. Do not collapse independent
dimensions into one score unless the aggregation rule is justified.

### 2. Define the target distribution

Describe the real workload before sampling benchmark cases.

Record the variables expected to affect difficulty, for example:

- task complexity;
- context size;
- number of tools or systems touched;
- language or domain;
- ambiguity;
- risk or severity;
- workflow duration;
- required autonomy;
- failure mode.

For each variable, state whether the benchmark should reproduce, stratify, or
intentionally oversample the production distribution.

### 3. Define the sampling plan

Specify:

- inclusion and exclusion rules;
- sampling frame;
- sample size target and rationale;
- stratification or oversampling rules;
- deduplication rules;
- train/dev/test or public/private partitioning;
- contamination and leakage controls.

If the target distribution is unknown, make that a validity risk rather than
silently substituting convenience sampling.

### 4. Define benchmark cases

Each case should have stable identifiers and enough provenance to reproduce the
input without exposing unrelated data.

Recommended case schema:

```yaml
case_id: string
source_provenance: string
input_ref: string
slice_labels:
  complexity: simple|medium|complex
  risk: low|medium|high
expected_evidence_ref: string|null
```

### 5. Define metrics and comparison rules

For every metric document:

- numerator and denominator;
- whether the denominator is fixed across systems;
- treatment of missing, failed, retried, or timed-out runs;
- aggregation across repeated stochastic runs;
- direction of improvement;
- known pathologies.

Prefer fixed-denominator metrics for cross-system ranking. Keep exploratory or
system-dependent metrics explicitly diagnostic.

### 6. Define slices

Pre-register slices that test meaningful capability boundaries. Avoid creating
slices only after observing favorable results.

### 7. Write the validity register

At minimum assess:

- construct validity;
- sampling/representativeness;
- ground-truth completeness;
- judge reliability;
- matcher reliability;
- contamination;
- stochastic variance;
- metric gaming;
- external or production validity.

For each risk, record evidence, mitigation, and residual uncertainty.

### 8. Freeze and version the contract

Version the dataset, rubric, matcher, judge configuration, metric definitions,
and reporting template. A score without the evaluation contract version is not
a reproducible result.

## Output contract

Produce a `benchmark-design.md` or equivalent structured artifact containing:

1. capability claim;
2. decision supported;
3. target population and target distribution;
4. sampling plan;
5. benchmark case schema;
6. primary metrics;
7. diagnostic metrics;
8. slices;
9. run protocol;
10. validity register;
11. versioning and change policy.

End with a short section named `Claims this benchmark can support` and another
named `Claims this benchmark cannot support`.

## Invariants

- A benchmark is a measurement instrument, not a dataset.
- The construct is defined before the metric.
- Sampling has an explicit target distribution.
- Cross-system metrics identify whether denominators are fixed.
- Failed runs are accounted for explicitly.
- Benchmark, judge, and system-under-test versions are recorded separately.
- Unknown validity properties remain visible as unknown.

## Failure and escalation conditions

Escalate or stop benchmark construction when:

- the capability claim cannot be made observable;
- the target population cannot be characterized at all;
- available cases are clearly convenience-biased but the benchmark will be
  presented as representative;
- the proposed metric rewards behavior contrary to the real decision;
- the benchmark will be used for high-stakes decisions without a human-reviewed
  validity assessment.

## Handoffs

Use:

- `eval-rubric-authoring` to operationalize quality judgments;
- `ground-truth-construction` to build the reference set;
- `benchmark-scorecard` to define final reporting;
- `benchmark-validity-audit` after implementation to test whether the design
  survived contact with the actual benchmark.

## Compact example

Question: "Which pull-request reviewer should we deploy?"

Bad design: sample 50 memorable bugs and count comments.

Better design: define review usefulness as valid issue discovery under an
acceptable false-positive burden; sample PRs across realistic size/language/
complexity strata; pre-register precision, grounded recall, critical-issue
recall, latency, cost, and failure rate; then separately audit judge accuracy
and production validity.
