---
name: agentic-test-topology
description: >-
  Place tests, fixtures, and reusable contracts at their owning boundary, move
  them with modules, and expand execution to affected test owners. Use when
  adding or relocating tests or deciding which suites a change affects.
---

# Agentic test ownership and topology

## Source

ADR-0025, *Agentic test ownership, placement, and execution topology*, is
canonical in [the architecture decision](https://github.com/rmax-ai/architecture/blob/main/decisions/0025-agentic-test-ownership-placement-and-execution-topology.md).
This skill carries its test and fixture ownership, placement, relocation, and
execution-topology guidance. It does not set a verification-sufficiency policy:
ADR-0023 remains authoritative for deciding whether evidence supports a claim.
Task provenance: `rmax-ai/delegation-queue#216`.

## Purpose

Give each test a clear owner and a stable place to live. Place the test with the
module, capability, repository contract, or system boundary whose behavior it
checks. Keep fixtures with the tests that own their meaning, and expand test
execution along real ownership and dependency edges.

This is a placement and affected-target guide, not a second test-adequacy
policy. It does not define coverage thresholds, confidence levels, required
gates, or when a claim is sufficiently verified. Use ADR-0023 for
claim-driven verification sufficiency.

## When to use

Use this skill when:

- adding a behavioral, cross-module, contract, integration, or acceptance test;
- deciding where a fixture or shared contract suite belongs;
- moving, splitting, or merging a module and its tests;
- selecting test owners affected by a source, contract, fixture, or tooling
  change;
- deciding whether an acceptance suite belongs in the product repository or an
  independent black-box harness.

## Required inputs

Collect, or mark as unknown:

- the observable behavior or public contract under test;
- the module and capability owners involved;
- the smallest boundary that can observe the behavior correctly;
- dependencies between changed modules and downstream consumers;
- who owns each fixture and reusable contract;
- available project, task, and test-runner mappings;
- whether an independent acceptance harness has its own owner and lifecycle.

## Decision procedure

### 1. State what the test observes

Describe the behavior, invariant, or contract from the observer's point of
view. Name the modules and boundary it crosses. Avoid beginning with a source
file, helper, or test framework, because those do not establish ownership.

### 2. Choose the owning boundary

Use the narrowest durable owner that can observe the behavior without reaching
through another owner's private implementation:

1. **Module behavior:** module behavioral tests belong with the module that owns
   the behavior. Keep them in its package or module, near its source and
   public-facing tests.
2. **Cross-module capability:** place the test at the nearest common owner of
   the participating modules or capability. It belongs to the capability that
   owns the collaboration, not whichever module happened to change last.
3. **Repository contract or integration:** place repository-wide contract and
   integration tests at the repo boundary. They verify shared contracts,
   composition, or wiring across repository-owned modules.
4. **Acceptance, E2E, or BDD behavior:** place the test at the system boundary.
   An independent black-box harness is appropriate when it has a distinct
   owner and lifecycle and tests through public interfaces rather than importing
   application internals.

If the boundary is ambiguous, identify the owner before adding another shared
test directory. If a test spans multiple levels, split it only when the parts
have distinct owners and each remains useful on its own.

### 3. Assign fixture ownership

Keep a fixture beside the test or contract that defines its meaning. Module
fixtures stay with module tests; cross-module fixtures stay with the nearest
common owner; repository-wide fixtures stay with the repo-level contract or
integration suite. A system harness owns its scenario data and environment.
Fixture ownership follows the same boundary as the behavior or contract it
describes.

Share a fixture only when its shape is a stable contract used by multiple
owners. Give that contract an explicit owner, keep one canonical copy, and let
consumers adapt it locally. Do not turn convenient fixture reuse into a giant
global fixture registry.

### 4. Reuse contract suites without coupling implementations

Define a reusable contract suite once at the boundary that owns the contract.
Run it against each implementation through a small adapter, factory, or
configuration hook. Keep expected behavior and contract fixtures independent
of implementation internals. Put a repository-wide suite under the repository
test boundary; put a module-owned public contract suite with that module.

### 5. Move tests with their owner

Move module behavioral tests and module-owned fixtures together with the module.
Update imports, test-runner configuration, project metadata, and affected-target
edges in the same relocation. Keep repository contract/integration tests at the
repo boundary and system acceptance tests at the system boundary. Move those
only when their actual owner or boundary changes; do not sweep every test into
the relocated module.

When a module splits, assign each test and fixture to its new owner. Keep
cross-module tests with the nearest common owner, and preserve external
contracts while adapting paths and runner configuration.

### 6. Expand affected-target execution

Use the repository's declared ownership and dependency graph when selecting
targets:

- include the changed module's behavioral tests;
- include the nearest-owner suites that exercise changed cross-module edges;
- include direct or transitive consumers whose public contract or behavior may
  be affected;
- expand to repository contract or integration owners when shared contracts,
  composition, schemas, fixtures, generated inputs, test support, runner
  configuration, or the project graph changes;
- include system-boundary acceptance owners when the externally observable
  system path changes.

Do not stop at the changed directory when its contract has affected consumers.
Do not add unrelated suites merely because they share a language or test
framework. Record the selected owners and the graph edges that justify the
expansion. This determines affected execution topology only; ADR-0023 decides
whether the resulting evidence is sufficient for a claim.

## Repository layout example

```text
repo/
  packages/
    inventory/
      src/
      tests/                    # inventory behavior and module contract
      test-support/             # inventory-owned fixtures
    pricing/
      src/
      tests/                    # pricing behavior
    order-flow/
      src/
      tests/
        capabilities/           # inventory + pricing collaboration
  tests/
    contracts/                  # repository-wide contract suites
    integration/                # repository composition and wiring
  acceptance-harness/
    scenarios/                  # system-level black-box acceptance
```

The example keeps each module's tests beside its ownership boundary. The
`order-flow` tests belong to the nearest common capability owner. The top-level
`tests/` directory is reserved for repository-wide contracts and integration,
not mirrored copies of every module's tests. The acceptance harness in
`acceptance-harness/scenarios/` interacts through a public interface and owns
its scenarios independently.

## Independent black-box harness criteria

Use an independent harness when all of the following are true:

- it has a named owner distinct from the implementation module;
- it exercises a system or deployable through a public API, protocol, CLI, or
  other supported interface;
- it can run without importing private implementation code or module test
  helpers;
- its environment, fixtures, and lifecycle can be managed independently;
- the same scenario can exercise another implementation or system revision
  without rewriting assertions to match internals.

A slow suite alone is not a reason to create another harness. If the test is
module behavior or capability collaboration, keep it with that owner. If the
independent boundary cannot be described, resolve ownership before splitting
the suite.

## Invariants

- Every test and fixture has an explicit owner.
- Module behavioral tests move with their module.
- Cross-module tests stay at the nearest common owner.
- Repository-wide contract and integration tests stay at the repo boundary.
- Acceptance, E2E, and BDD tests exercise the system boundary or an independent
  black-box harness.
- A reusable contract suite has one owner and does not encode implementation
  internals.
- Affected execution follows declared ownership and dependency edges.
- Test placement never substitutes for ADR-0023 verification sufficiency.

## Anti-patterns

**Wrong:** defaulting to mirrored `src/` and root `tests/` trees when every
change must search and coordinate across both.
**Right:** keep module behavior tests inside their owning package, unless a
repository convention preserves ownership just as clearly.

**Wrong:** putting every domain fixture in one giant global fixture registry.
**Right:** keep fixtures with their owner and promote only stable, shared
  contract fixtures with explicit ownership.

**Wrong:** treating implementation-coupled tests that assert private helper
calls or internal object layout as the default.
**Right:** assert the observable behavior or public contract, and keep
implementation-specific tests local to the module that owns those details.

**Wrong:** placing a cross-capability test in the module that happened to be
edited first.
**Right:** place it at the nearest common owner of the participating modules.

**Wrong:** leaving module tests behind when relocating or splitting the module.
**Right:** move owned tests and fixtures with it, update runner metadata, and
  retain cross-owner suites at their own boundaries.

**Wrong:** running only the changed module after changing a shared contract or
  test-runner graph.
**Right:** expand to the affected consumers and test owners shown by the graph;
  let ADR-0023 determine verification sufficiency.

## Verification checklist

- [ ] The behavior or contract is described from an observer's point of view.
- [ ] The test has an explicit module, capability, repo, or system owner.
- [ ] Cross-module tests live at the nearest common owner.
- [ ] Repository-wide contract and integration tests live at the repo boundary.
- [ ] Acceptance tests use a system boundary or meet independent harness
      criteria.
- [ ] Fixtures live with their owning tests or stable contracts.
- [ ] Reusable contract expectations exist once and run against each
      implementation.
- [ ] Module relocation includes its tests, fixtures, and runner metadata.
- [ ] Affected targets include relevant consumers and shared test owners.
- [ ] Verification sufficiency is decided under ADR-0023, not inferred from
      placement.

## Failure and escalation

Stop and resolve ownership before adding tests when:

- two modules claim the same behavior or fixture;
- a cross-module test has no identifiable nearest common owner;
- the proposed suite requires private imports across module boundaries;
- an independent harness has no separate owner, public interface, or lifecycle;
- the affected-target graph cannot identify consumers of a changed contract.

Do not create a central directory or fixture registry to hide an unresolved
ownership decision.

## Handoffs

- `agent-native-modular-architecture` — identifies capability ownership and
  module boundaries.
- `machine-readable-capability-graph` — supplies declared owners and dependency
  edges.
- `affected-polyglot-toolchain` — maps affected projects to executable tasks.
- ADR-0023 — remains authoritative for claim-driven verification sufficiency.

## Compact example

An inventory module changes the public availability contract used by
`order-flow`. Keep inventory behavior tests and inventory-owned fixtures in
`packages/inventory/`. Keep the collaboration test in
`packages/order-flow/tests/capabilities/`, and expand execution to the affected
order-flow and downstream owners. A repository-wide contract suite belongs in
`tests/contracts/`; a customer journey belongs in the black-box acceptance
harness. The placement rule identifies owners and affected targets. ADR-0023,
not this skill, decides whether the evidence is sufficient for the claim.
