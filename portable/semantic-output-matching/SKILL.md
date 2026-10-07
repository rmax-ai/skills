---
name: semantic-output-matching
description: >-
  Match candidate-system outputs to reference items by semantic equivalence
  while keeping equivalence separate from correctness. Use to compute
  reference-based recall and prevent wording differences from becoming scoring
  errors.
---

# Semantic output matching

## Purpose

Determine whether a candidate output corresponds to an existing reference item.

Matching answers:

> Does this output express the same underlying claim or result as that reference?

Matching does not answer whether either item is correct. Correctness belongs to
the adjudication stage.

## When to use

Use this skill when outputs are open-ended or natural-language and exact string
matching would undercount equivalent results.

Typical cases:

- code-review findings;
- extracted research claims;
- security findings;
- compliance observations;
- bug reports;
- generated test diagnoses.

## Required inputs

- normalized candidate outputs;
- reference/gold items;
- stable case identifiers;
- equivalence policy;
- location/entity metadata where relevant;
- matcher implementation or human matching process.

## Procedure

### 1. Normalize to atomic items

Split multi-claim outputs before matching. Preserve raw text and candidate IDs.

### 2. Define equivalence

Document what must be shared for two items to match.

Possible dimensions:

- same underlying defect/fact;
- same affected entity or code region;
- same causal mechanism;
- same corrective implication.

Do not require identical wording or severity labels unless severity is part of
the reference identity.

### 3. Generate candidate pairs

Restrict comparisons within the same benchmark case. Use deterministic
location/entity filtering where available, then semantic matching.

Avoid comparing every output against unrelated cases.

### 4. Classify pair relations

Recommended relation set:

```text
equivalent
partial
different
uncertain
```

Use `equivalent` only when one reference item would make counting the candidate
as an additional independent discovery incorrect.

Use `partial` when claims overlap but one contains a materially distinct
condition, consequence, or sub-issue.

### 5. Resolve many-to-many cases

Prefer an explicit matching policy:

- one candidate may match at most one reference item for recall accounting;
- multiple duplicate candidates may map to one reference but count once for
  recall;
- duplicate output burden may still reduce precision or a separate noise metric.

Record the assignment algorithm and tie-breaking order.

### 6. Preserve unmatched outputs

Unmatched is not synonymous with false.

Route unmatched outputs to `novel-finding-adjudication` when the reference set
may be incomplete.

### 7. Validate the matcher

Create a human-labeled pair set containing:

- easy equivalents;
- paraphrases;
- nearby but distinct findings;
- partial overlaps;
- location collisions;
- adversarial lexical similarity.

Report confusion by relation type, not only aggregate accuracy.

## Output contract

Produce a deterministic mapping artifact:

```yaml
candidate_id: string
reference_id: string|null
relation: equivalent|partial|different|uncertain
matcher_version: string
evidence: string|null
```

Also report:

- matched unique references;
- duplicate candidate mappings;
- partial/uncertain count;
- unmatched candidate IDs.

## Invariants

- Matching and correctness are separate.
- Match comparisons stay within the same case.
- Duplicate candidate outputs do not inflate recall.
- Unmatched does not mean false.
- Matcher version is recorded with every result.
- Ambiguous pairings remain auditable.

## Failure and escalation conditions

Escalate when:

- one natural-language output contains multiple claims that were not split;
- the equivalence rule changes during system comparison;
- automated matching disagreement is concentrated in a high-value slice;
- the matcher depends primarily on lexical overlap for semantic tasks;
- many-to-many resolution changes leaderboard ordering.

## Handoffs

Use:

- `novel-finding-adjudication` for unmatched outputs;
- `llm-judge-calibration` if an LLM performs matching;
- `benchmark-stability-test` to test ranking sensitivity to matcher choice;
- `benchmark-scorecard` for final matched-recall accounting.

## Compact example

Reference: "The new cache key ignores tenant ID, so values can leak across
tenants."

Candidate A: "Cache entries are not namespaced per tenant." -> `equivalent`.

Candidate B: "Cache expiration is too long." -> `different`.

Candidate C: "The cache implementation is unsafe." -> `uncertain` unless the
output provides the same specific mechanism.
