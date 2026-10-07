---
name: ground-truth-construction
description: >-
  Construct high-recall benchmark ground truth from heterogeneous discovery
  sources, deduplicate candidates, adjudicate them under one rubric, preserve
  provenance, and quantify residual incompleteness. Use when a reference set
  cannot be assumed complete.
---

# Ground-truth construction

## Purpose

Build a defensible reference set for an evaluation benchmark without confusing
"what existing annotators found" with truth.

The method is recall-oriented: use heterogeneous sources to discover candidate
truth, then apply one shared adjudication standard. Discovery sources may be
noisy. They do not become authoritative merely because they are human, model,
tool, or historical outputs.

## When to use

Use this skill when:

- correctness depends on finding multiple valid items;
- the reference set is likely incomplete;
- humans, deterministic tools, historical outcomes, and models can each reveal
  different evidence;
- benchmark false positives may actually be novel valid discoveries.

Do not use a single generator as both candidate source and final adjudicator
without documenting the circularity.

## Required inputs

- benchmark cases and stable case identifiers;
- an adjudication rubric from `eval-rubric-authoring`;
- available discovery sources;
- rules for semantic deduplication;
- provenance requirements;
- human escalation policy.

## Procedure

### 1. Define discovery source classes

Prefer heterogeneous source classes rather than many variants of the same
source.

Examples:

- prior human findings;
- subsequent fixes or observed outcomes;
- deterministic/static analysis;
- multiple independently prompted model families;
- domain-specific validators;
- expert review.

Record source identity and version for every candidate.

### 2. Generate a high-recall candidate pool

Run each source independently where possible. Keep the raw candidate before any
merging.

Recommended candidate record:

```yaml
candidate_id: string
case_id: string
source_type: human|history|tool|model|expert
source_id: string
finding: string
evidence: [string]
location: string|null
created_at: string|null
```

Do not discard candidates solely because only one source found them.

### 3. Normalize representation

Convert findings into atomic claims. Split comments that contain multiple
independent claims. Preserve the raw source text for auditability.

Normalize locations, entities, and evidence references without changing the
semantic claim.

### 4. Deduplicate semantically

Group candidates that express the same underlying issue or fact.

Deduplication answers:

> Are these candidates about the same thing?

It does not answer:

> Is this thing true?

Keep those decisions separate.

Each cluster should retain all source provenance and a canonical statement.

### 5. Adjudicate every canonical candidate

Apply the same rubric regardless of discovery source.

Record:

- pass/fail or label;
- severity/category when relevant;
- evidence used;
- confidence if the process requires it;
- adjudicator identity/version;
- reason for rejection.

For ambiguous cases, use the rubric's escalation path rather than forcing
consensus.

### 6. Build the gold set

Include adjudicated valid canonical findings. Preserve rejected findings in an
audit log so future changes to the rubric can be replayed.

Recommended gold record:

```yaml
gold_id: string
case_id: string
claim: string
evidence: [string]
severity: string|null
category: string|null
discovered_by: [string]
rubric_version: string
adjudication_version: string
```

### 7. Estimate residual incompleteness

Ground truth is rarely provably complete. Measure evidence of saturation rather
than claiming completeness.

Useful diagnostics:

- unique valid findings contributed by each source;
- marginal yield of the final discovery source;
- overlap matrix among sources;
- percentage of gold findings supported by multiple source classes;
- novel valid findings discovered during later candidate-system evaluation.

If later systems repeatedly discover valid unmatched findings, treat that as
evidence that the reference set is incomplete.

### 8. Freeze and version

Version the candidate pool, deduplication decisions, rubric, adjudication output,
and gold set separately.

## Output contract

Produce:

- `candidate-findings.*`;
- `dedup-clusters.*`;
- `gold-findings.*`;
- `rejected-findings.*`;
- `ground-truth-report.md`.

The report must state discovery sources, adjudication process, saturation
evidence, known blind spots, and whether ground truth should be treated as
closed or open-ended.

## Invariants

- Discovery maximizes recall; adjudication defines validity.
- No source class is truth by definition.
- Raw provenance survives deduplication.
- Semantic deduplication is not correctness judging.
- Rejected candidates remain auditable.
- Ground-truth completeness is measured as evidence, not asserted by default.

## Failure and escalation conditions

Escalate when:

- the same model family generates and judges most of the gold set;
- the adjudication rubric is too vague to resolve common candidates;
- source overlap is extremely high and likely reflects shared blind spots;
- cases lack enough evidence for adjudication;
- provenance cannot be preserved.

## Handoffs

Use:

- `semantic-output-matching` to compare system findings against the gold set;
- `novel-finding-adjudication` for unmatched candidate-system outputs;
- `benchmark-validity-audit` to assess completeness and circularity.

## Compact example

For code review, combine human review comments, later author fixes, static
analysis, and independent model reviewers. Deduplicate "missing null check" and
"possible None dereference" as one claim. Then judge that canonical claim under
one rubric. The fact that three sources mentioned it increases discovery
confidence, but does not replace adjudication.
