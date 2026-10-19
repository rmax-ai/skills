---
name: agentic-verification-ladder
description: >-
  Select verification gates V0-V5 from change class and the affected graph,
  test behavior and contracts instead of implementation shape, and emit compact
  machine-readable evidence. Use when deciding what a change must run, judging
  whether a green suite means anything, or recording PR evidence.
---

# Agentic verification ladder

## Source

ADR-0021, *Verification ladder and evidence contract for agentic software
development*, merged in `rmax-ai/architecture#15` (merge commit `6fbba39`).
Related: ADR-0008, ADR-0009, ADR-0014, ADR-0018, ADR-0020.

## Purpose

Make verification fast enough for autonomous throughput and strict enough to
stay safe. The failure mode to avoid is an agent choosing the tests it expects
to pass; the other failure mode is running the entire suite for every edit.

Gate selection is derived from declared architecture and change class. Test
*design* is derived from behavior, contracts, and invariants.

## When to use

Use this skill when:

- a change is ready to verify and you must decide what to run;
- a suite is green but you doubt it proves the claim;
- writing tests for a new capability or adapter;
- producing PR or handoff evidence;
- a gate fails and someone proposes downgrading it to a warning.

## Required inputs

Collect, or state as unknown:

- `change_class`: L0-L3 from `change-envelope-planning`;
- `affected_projects`: from the Moon affected graph;
- `contracts`: public APIs or schemas the change touches;
- `risk`: security, data, migration, or control-plane sensitivity;
- `existing_gates`: which V-levels the repository can already run;
- `acceptance_stories`: externally meaningful outcomes expected of the change.

## Procedure

### 1. Work up the ladder from cheapest to broadest

```text
V0  changed-file hygiene
    format, parse/compile, basic static checks on touched inputs

V1  owning project/module
    lint, type/compiler checks, behavior tests for the affected module

V2  contract boundary
    public API/schema/adapter conformance and compatibility tests

V3  affected dependents
    direct or deep downstream projects selected from the dependency graph

V4  repository/system
    broader integration/end-to-end/full-suite verification

V5  runtime evidence
    canary, production telemetry, replay, or system-level acceptance when applicable
```

A change does not automatically run every level. Required levels come from
class, affected graph, risk, and repository policy.

### 2. Apply the default class mapping

```text
L0 -> V0 + V1
L1 -> V0 + V1 + relevant V2 + direct affected V3
L2 -> V0 + V1 + V2 + affected V3 + relevant V4
L3 -> V0..V4 plus explicit rollout/runtime evidence when applicable
```

Security-, data-, migration-, or control-plane-sensitive changes may require
stronger gates regardless of class.

### 3. Let the graph determine scope

Use the Moon task and project graph to derive affected projects and downstream
dependents. An agent may recommend an additional test; it must not reduce the
computed scope without an explicit recorded exception. Global, toolchain,
lockfile, and contract changes conservatively expand verification.

### 4. Test behavior, contracts, and invariants

Prefer tests that answer:

- does the consumer-observable behavior hold?
- does the public contract remain valid?
- do domain invariants hold across meaningful cases?
- does the adapter conform to its port contract?
- does the acceptance story work end to end at the smallest useful boundary?

Avoid tests whose primary assertion is that private helper A calls private
helper B, or that re-implement the algorithm in test code.

### 5. Avoid low-information fixtures

Hard-coded examples suit precise edge cases and regressions, but a suite must
not consist mainly of tiny fixtures encoding the same assumptions as the
implementation. Where useful, add property-based tests for invariants,
table-driven boundary cases, realistic sanitized fixtures, replayed historical
failures, contract fixtures shared across implementations, differential tests
against a trusted reference, and mutation or fault tests for critical
validators and policies.

Add complexity only when it increases defect-detection power.

### 6. State acceptance stories before implementing

```text
Given a new SearchProvider implementation,
when the search capability invokes it with a valid request,
then it returns the canonical result type,
handles timeout/cancellation according to the provider contract,
and existing providers remain behaviorally unchanged.
```

Acceptance stories may be automated tests, replay scripts, or deterministic
command checks. Write them in the plan, not after the fact.

### 7. Make contract suites reusable

For interchangeable providers or adapters, define one conformance suite and run
it against every implementation. That is what lets an agent add or replace an
implementation without duplicating expectations or binding tests to internals.

### 8. Emit machine-readable evidence

```yaml
schema_version: 1
base_revision: <sha>
head_revision: <sha>
change_class: L1
affected_modules:
  - search
verification:
  - gate: V1
    task: search:test
    result: pass
  - gate: V2
    task: search:contract
    result: pass
  - gate: V3
    task: api:test
    result: pass
skipped:
  - gate: V4
    reason: not-required-by-policy
```

Raw logs may live separately. Durable review state holds the summary and
references, so later agents are not forced to read whole logs.

### 9. Fail visibly and classify the failure

Do not convert a failing gate into a warning to keep throughput high. Classify
the source where possible:

```text
implementation defect
contract incompatibility
unrelated/pre-existing failure
environment/tooling failure
flaky/indeterminate verification
```

Only the affected task may be quarantined; unrelated work continues when the
control plane can prove isolation.

### 10. Place full-suite runs strategically

Use full repository or system verification at release and integration gates,
for high-impact L2/L3 changes, for periodic drift detection, for graph and
tooling changes, and to calibrate affected-only confidence. Track whether
affected-only runs miss failures later found by full runs, and feed that back
into project inputs and dependency metadata.

### 11. Measure verification cost

Record where feasible: wall time, CPU/memory class, cache hit or miss, projects
and tasks executed, failure class, and agent or model tokens spent after
verification failures. Optimize cost per safely integrated change, not shortest
CI time.

### 12. Delete tests that stop adding information

A redundant, implementation-coupled, flaky, or superseded test may be removed
when stronger behavior or contract coverage proves the same property. Test count
and coverage percentage are diagnostics, not objectives.

## Invariants

- Gates are selected from class and graph, never from expected outcomes.
- An agent may add verification scope, never silently reduce it.
- Contracts are verified at their boundary, by every implementation.
- Evidence is compact, versioned, and references the exact revisions.
- Skipped gates carry a reason; failures are never warnings.
- Behavior tests survive internal refactors; implementation-shaped tests do not.
- Full-suite runs calibrate affected-only confidence.

## Anti-patterns

**Wrong:** running only the tests that fail-free in the first attempt.
**Right:** derive the required set, then report any additional local run.

**Wrong:** `assert service._repo.called_once` as the main assertion.
**Right:** assert the observable outcome and the domain error for the failure path.

**Wrong:** "V4 was slow, so we skipped it" on an L2 contract change.
**Right:** record the skip with a policy reason, or run the gate.

**Wrong:** 40 single-case fixtures that mirror the implementation's branches.
**Right:** a table of boundary cases, an invariant property test, and one
realistic fixture replayed from a real failure.

**Wrong:** pasting a 4,000-line log into the PR.
**Right:** the evidence record plus a pointer to the retained log.

## Verification checklist

- [ ] Change class and affected projects are recorded.
- [ ] Required V-levels are listed with the task that satisfies each.
- [ ] Any skipped gate states a policy reason.
- [ ] Every changed public contract has a V2 conformance run.
- [ ] Affected dependents ran at V3, or the exception is recorded.
- [ ] Tests assert behavior, contracts, or invariants, not call order.
- [ ] The evidence record names base and head revisions.
- [ ] No failing gate was downgraded or retried into green.

## Failure and escalation

Escalate when:

- the computed scope omits a module the change demonstrably affects;
- a required gate cannot run in the current environment;
- a failure class is ambiguous between implementation defect and environment;
- a task needs to reduce scope below policy for any reason;
- evidence cannot be produced in machine-readable form.

## Handoffs

- `change-envelope-planning` — supplies class and allowed mutation surface.
- `affected-polyglot-toolchain` — supplies affected projects and canonical tasks.
- `machine-readable-capability-graph` — maps modules to verification tasks.
- `pydantic-boundary-validation`, `zod-boundary-validation` — boundary-contract
  test design.
- `token-efficient-repository-context` — keeps evidence and review context small.

## Compact example

An L1 adapter addition produces: V0 ruff format and check on touched files; V1
`search:test`; V2 `search:contract` run against both the new and existing
providers; V3 `api:test` because the app depends on the contract. V4 is skipped
with `not-required-by-policy`. The evidence record names base and head shas, and
the reviewer reads the record plus the diff instead of the logs.
