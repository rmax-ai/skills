---
name: llm-judge-calibration
description: >-
  Calibrate an LLM evaluator against human-adjudicated examples, measure
  disagreement by label and slice, diagnose systematic bias, and define a safe
  automation threshold. Use before trusting model-based benchmark judgments.
---

# LLM judge calibration

## Purpose

Test whether an automated judge is a sufficiently faithful implementation of a
rubric for the decisions it will make.

An LLM judge is part of the measurement instrument. Its errors must be measured
independently from the candidate system.

## When to use

Use this skill whenever an LLM:

- labels candidate outputs;
- assigns severity or categories;
- decides pass/fail;
- performs semantic matching;
- adjudicates novel findings;
- produces scores used for model/system comparison.

## Required inputs

- frozen rubric version;
- human-adjudicated calibration set;
- judge prompt and model/configuration version;
- allowed evidence;
- important benchmark slices;
- cost and latency constraints.

## Procedure

### 1. Build a calibration set

Sample examples across:

- positive and negative labels;
- boundary cases;
- severity levels;
- categories;
- benchmark slices;
- known disagreement cases.

Do not evaluate only easy examples.

### 2. Freeze the human reference

Use independent human adjudication where stakes justify it. Preserve
disagreements and final resolution.

Human labels are not automatically perfect; document adjudication quality.

### 3. Run the judge reproducibly

Record:

- model/provider identifier;
- prompt/rubric version;
- temperature or sampling settings;
- tool/context configuration;
- retries and failure handling.

Run repeated trials if the judge is stochastic.

### 4. Compute decision metrics

For binary decisions report at least:

- confusion matrix;
- accuracy;
- positive-class precision;
- positive-class recall;
- false-positive rate;
- false-negative rate.

For ordinal/categorical labels report exact agreement and a confusion matrix.
Do not hide weak severity agreement behind strong binary agreement.

### 5. Slice disagreements

Measure agreement by dimensions such as:

- category;
- severity;
- complexity;
- context size;
- language/domain;
- evidence type.

A judge with high overall agreement may still be unsafe on the cases that
matter most.

### 6. Diagnose systematic bias

Inspect false positives and false negatives.

Common patterns:

- verbosity bias;
- agreeing with confident wording;
- severity inflation;
- preference for familiar categories;
- failure on long context;
- using external assumptions not allowed by the rubric.

### 7. Define the automation boundary

Choose one:

- fully automated;
- automated except specified slices;
- confidence/consensus gated;
- human-first.

Tie the decision to measured error and consequence, not convenience.

### 8. Recalibrate after changes

Any meaningful change to model, prompt, rubric, context assembly, or tool access
can invalidate prior calibration.

## Output contract

Produce a `judge-calibration-report.md` with:

1. calibration set composition;
2. human reference process;
3. judge configuration;
4. overall confusion matrix;
5. per-label metrics;
6. slice metrics;
7. disagreement examples;
8. identified biases;
9. approved automation boundary;
10. recalibration triggers.

## Invariants

- Judge calibration is independent from candidate-system performance.
- The rubric version is frozen during comparison.
- Overall agreement never substitutes for slice analysis.
- Exact label agreement is reported for severity/category tasks.
- Judge failures and retries are included in operational metrics.
- Calibration is invalidated by material judge configuration changes.

## Failure and escalation conditions

Require human review when:

- false positives or false negatives exceed the tolerated burden;
- disagreement concentrates in high-severity cases;
- the judge uses evidence outside the allowed context;
- repeated judge runs materially disagree;
- a new model/prompt has not been calibrated.

## Handoffs

Use:

- `benchmark-stability-test` to compare rankings across alternative judges;
- `benchmark-validity-audit` to assess evaluator dependence;
- `benchmark-scorecard` to disclose judge calibration alongside benchmark results.

## Compact example

Suppose a judge agrees with humans on 97% of binary validity decisions but only
63% of severity labels. It may be acceptable for validity classification while
severity-sensitive routing remains human-reviewed. One aggregate agreement
number would hide that distinction.
