---
name: claim-driven-software-verification
description: >-
  Map software claims to verification obligations by risk, select evidence
  across affected scope, and record decisions with residual risk.
---

# Claim-Driven Software Verification

## Source

This skill operationalizes ADR-0023, *Claim-driven software verification for
agentic development at scale*, from `decisions/0023-claim-driven-software-verification-for-agentic-development.md`.
The accepted review of `rmax-ai/architecture#18` named this capability as
missing.

## Purpose

Use claims as the unit of verification. For each meaningful change, connect
the claim to a verification obligation, supporting evidence, a decision, and
the residual risk that remains.

Verification means establishing evidence that required properties, contracts,
invariants, and acceptance criteria hold. A test is an executable experiment
under selected conditions and one evidence class among several. Formal
verification remains a distinct, stronger class when mathematical proof or
model checking is appropriate. A passing test suite or increased coverage
alone does not establish verification sufficiency.

The objective is verification sufficiency per unit cost. Select the smallest
strong set of evidence that supports the claims at their risk level.

## When to use

Use this skill for every non-trivial software change that introduces or could
invalidate behavior, contracts, invariants, or acceptance criteria.

Use it when planning verification, reviewing a green result, recording a
handoff, or deciding whether available evidence is sufficient.

For documentation or non-semantic metadata, use relevant formatting, schema,
and link validation. Do not invent behavioral obligations when none changed.

This skill does not define test file placement, a universal test framework,
or the design of probabilistic agent evaluations. Hand off those questions
as described in Handoffs.

## Procedure

1. Read the change, its acceptance criteria, and the affected project graph.
   Record unknown inputs as unknown; do not infer evidence that was not run.

2. Derive claims from changed behavior and affected contracts. Include every
   property that must remain true after the change. Do not derive claims from
   implementation structure alone.

3. For each claim, write one verification obligation that states the property
   to establish. Record its risk using blast radius and uncertainty.

4. Map each change shape to its minimum expected evidence:

   | Change shape | Minimum expected evidence |
   | --- | --- |
   | Documentation or non-semantic metadata | Formatting, schema, and link validation as applicable |
   | Local pure logic | Targeted behavioral tests; property tests when useful |
   | Public API or protocol | Contract or schema validation plus compatibility or integration evidence |
   | Persistence or migration | Forward and backward compatibility plus representative migration or replay |
   | Scheduler, queue, or concurrency | Invariants plus deterministic, property, concurrency, or replay evidence |
   | Security or governance boundary | Positive and negative authorization cases plus static or policy checks |
   | User-visible multi-component workflow | Acceptance or end-to-end evidence at the narrowest representative scope |
   | Environment-dependent runtime behavior | Pre-merge evidence plus bounded post-deploy canary or telemetry evidence |

5. Use the evidence ladder to select classes that can establish each
   obligation, from cheaper or local to broader or stronger as the claim
   requires:

   1. Compiler, type-system, and schema validation.
   2. Linting and static analysis.
   3. Deterministic unit or component tests.
   4. Property-based, fuzz, and metamorphic tests.
   5. API or protocol contract tests.
   6. Integration tests across real boundaries.
   7. Acceptance, BDD, or end-to-end workflow tests.
   8. Replay, migration, and compatibility tests.
   9. Fault injection, concurrency, and recovery tests.
   10. Security analysis and adversarial negative tests.
   11. Formal proof, model checking, or SMT-based verification where justified.
   12. Canaries, production invariants, telemetry, and SLO evidence when
       pre-merge evidence cannot reproduce the environment.

6. Match evidence to the claim. A type checker may discharge a type contract
   and be irrelevant to a persistence invariant. High-risk claims should have
   at least one evidence source not simply derived from the implementation.

7. Start with cheap deterministic checks for directly affected modules and
   contracts. Expand the scope when dependency edges, public interfaces,
   persistence, security boundaries, or high-risk invariants are touched.
   Use full-repository or full-system suites as escalation, not as the default
   for every local edit.

8. Prefer checks of externally meaningful behavior, contracts, and invariants.
   Use mocks at true expensive, nondeterministic, unsafe, or unavailable
   boundaries. Do not use mocks instead of integration evidence when boundary
   compatibility is itself the claim.

9. Run the selected evidence and preserve the inputs, environment assumptions,
   versions, and seeds that affect reproducibility. Do not invent evidence.

10. Record a compact verification record for every non-trivial change:

    - claims: what must be true;
    - risk: why each claim matters and its expected blast radius;
    - evidence: command, artifact, test, static result, replay, trace, or
      runtime signal;
    - result: pass, fail, or not run, with relevant bounded output;
    - decision: whether evidence is sufficient for the obligation;
    - residual risk: uncertainty that remains.

    The record may live in the delegation task, PR body, evidence bundle, or
    another machine-readable artifact. A repository may require a stricter
    schema, but it must preserve the claim-to-evidence mapping.

11. Stop only when every required claim has evidence sufficient for its risk,
    no required evidence is failing or unknown without explicit approval,
    added checks give materially diminishing information for their cost, and
    residual risks are explicit and acceptable under repository policy.

12. If an environment-dependent claim cannot be established in isolation,
    include bounded runtime evidence such as a canary, shadow traffic,
    invariant monitor, trace, SLO, or rollback check when applicable. This
    complements pre-merge evidence; it does not excuse weak pre-merge evidence.

## Invariants

- Preserve the chain: claim → verification obligation → evidence → decision →
  residual risk.
- Every meaningful change has claims derived from behavior and affected
  contracts, not from internal structure.
- Evidence strength is specific to the obligation it supports.
- Tests are one evidence class among many, not the only verification method.
- No coverage target and no test-count target exist. Coverage may diagnose
  unexercised areas, but it is not the primary acceptance target.
- Prefer coverage of verification obligations over coverage of executable
  lines; line coverage is a diagnostic signal only.
- A change may add no test when stronger existing evidence already discharges
  its obligations.
- Verification follows the smallest affected closure that gives sufficient
  confidence; expand it when risk or dependency scope requires.
- High-risk claims should have evidence that is not simply derived from the
  implementation under test.

## Anti-patterns

**Wrong:** Treat a green suite or a coverage increase as sufficient by itself.
**Right:** Map each claim to evidence that establishes its obligation.

**Wrong:** Add tests whose only purpose is increasing line or branch counts.
**Right:** Add evidence only when it covers an obligation or failure mode.

**Wrong:** Duplicate implementation data in brittle tests or assert incidental
private call order.
**Right:** Assert stable behavior and contracts at the narrowest useful
boundary.

**Wrong:** Use repeated retries or majority vote to turn flaky evidence into a
pass.
**Right:** Restore reliability or replace it with stronger evidence.

**Wrong:** Run the full system for every local change without an affected-scope
reason.
**Right:** Start with the directly affected closure and expand on risk signals.

## Verification checklist

- [ ] Claims describe changed behavior, contracts, and invariants.
- [ ] Each claim has a clear verification obligation.
- [ ] Risk and expected blast radius are recorded for each claim.
- [ ] Evidence classes match the obligations and their risk.
- [ ] The affected scope starts narrow and expands for relevant dependencies.
- [ ] Tests are treated as evidence, not as the objective.
- [ ] Missing, failing, flaky, or unreproducible required evidence fails closed.
- [ ] Results and relevant bounded output are recorded.
- [ ] Residual risk and the verification decision are explicit.
- [ ] The stopping rule is met before verification is declared sufficient.

## Failure and escalation

Use fail closed handling when required evidence is missing, failing, flaky, or
unreproducible. The affected obligation remains unsupported and its claim is
not verified. Report the missing evidence and residual risk explicitly.

A flaky check cannot satisfy an obligation until reliability is restored or a
stronger replacement source is provided. Retries may diagnose nondeterminism;
they cannot turn an intermittent failure into a pass by majority vote.

If a check cannot run, record it as not run. Do not invent a result. If a
required result is failing or unknown, do not mark the change verified without
explicit approval under the repository's merge or deploy policy.

Escalate verification when affected dependencies, interfaces, persistence,
security boundaries, or high-risk invariants require broader evidence. Review
missing obligations before requesting arbitrary additional tests.

## Handoffs

Use `change-envelope-planning` to resolve change class and planned scope. Use
`agentic-verification-ladder` for operational gate selection and machine-readable
verification records.

Hand off test file placement and topology questions to ADR-0025,
`agentic-test-ownership-placement`. This skill does not duplicate that
decision.

Hand off probabilistic evidence questions to ADR-0026,
`probabilistic-agent-evaluation`. This skill does not duplicate that
decision.
