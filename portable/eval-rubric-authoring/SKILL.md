---
name: eval-rubric-authoring
description: >-
  Convert a vague quality concept into a versioned, operational evaluation
  rubric with observable criteria, boundary cases, evidence requirements, and
  escalation rules. Use before human or LLM judging.
---

# Evaluation rubric authoring

## Purpose

Create the semantic contract that defines what counts as success, failure, and
important subtypes in an evaluation.

A judge model is an implementation detail. The rubric is the actual
specification.

## When to use

Use this skill before:

- human annotation;
- LLM-as-judge evaluation;
- building benchmark ground truth;
- comparing candidate outputs;
- assigning severity, category, completeness, or policy labels.

Use it again when judge disagreements reveal ambiguous criteria.

## Required inputs

- capability claim from `benchmark-design`;
- concrete examples of desired and undesired behavior;
- downstream metric needs;
- risk/severity taxonomy if applicable;
- evidence available to adjudicators.

## Procedure

### 1. Define the decision unit

State exactly what is being judged.

Examples:

- one atomic finding;
- one task trajectory;
- one answer;
- one tool call;
- one completed workflow.

Avoid rubrics that silently alternate between item-level and case-level quality.

### 2. Define observable criteria

Each criterion must be answerable from allowed evidence.

Prefer atomic fields such as:

```yaml
valid: boolean
relevant: boolean
non_trivial: boolean
complete: boolean
policy_compliant: boolean
severity: low|medium|high|critical
category: correctness|security|performance|maintainability|other
```

Only include fields that change a decision or support analysis.

### 3. Specify evidence boundaries

Document what the adjudicator may inspect.

For each criterion state:

- admissible evidence;
- forbidden assumptions;
- whether external lookup is allowed;
- how missing evidence is treated.

A judge should not reward plausible speculation when the benchmark requires
grounded evidence.

### 4. Write pass/fail definitions

Use positive definitions and exclusion rules.

Example:

`valid=true` when the claim is factually supported by the provided code and
context and identifies a real defect or requirement violation.

`valid=false` when the claim is contradicted, unsupported, purely stylistic
outside scope, or duplicates another atomic claim.

### 5. Add boundary examples

For every criterion include:

- clear positive;
- clear negative;
- near-boundary positive;
- near-boundary negative;
- ambiguous case and expected escalation.

Boundary examples are more valuable than many easy examples.

### 6. Define severity independently from validity

A false critical finding is still false. Do not let severity influence the
initial truth judgment.

Severity definitions should refer to consequences, scope, recoverability, and
likelihood rather than emotional wording.

### 7. Define category taxonomy

Categories should be mutually interpretable and useful for slicing. Include an
`other` or escalation path when forcing a category would create noise.

### 8. Define adjudication and tie-breaking

Specify:

- single judge versus multiple judges;
- when a human is required;
- how disagreement is recorded;
- whether majority vote is permitted;
- how rubric defects are distinguished from annotator errors.

Never erase disagreement data.

### 9. Version the rubric

Treat rubric changes as benchmark changes. Record the version in every judged
artifact.

## Output contract

Produce a rubric document with:

1. decision unit;
2. criteria table;
3. evidence policy;
4. pass/fail definitions;
5. severity definitions;
6. category definitions;
7. boundary examples;
8. escalation rules;
9. disagreement protocol;
10. version/change log.

Also produce a compact machine-readable schema when structured judging is
required.

## Invariants

- Rubric precedes judge selection.
- Criteria are observable from allowed evidence.
- Validity is independent from severity.
- Matching/equivalence is not correctness.
- Ambiguity has an explicit escalation path.
- Changes are versioned and can trigger re-adjudication.

## Failure and escalation conditions

Stop and revise the rubric when:

- annotators repeatedly ask for unstated assumptions;
- two reasonable judges interpret a core criterion differently;
- a field cannot be grounded in available evidence;
- categories overlap so heavily that assignments are arbitrary;
- the scoring rule rewards verbosity instead of quality.

## Handoffs

Use:

- `llm-judge-calibration` to test whether an automated judge implements the
  rubric faithfully;
- `ground-truth-construction` to adjudicate candidate truth;
- `benchmark-validity-audit` when rubric ambiguity threatens construct validity.

## Compact example

Weak criterion: "Is this review comment useful?"

Operational criterion:

```yaml
valid: claim is supported by the changed code and context
relevant: claim concerns the proposed change or its direct consequences
non_trivial: claim is more than preference or obvious restatement
```

A comment is accepted only if all three are true. Severity is assigned
afterwards.
