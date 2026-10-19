---
name: agent-native-modular-architecture
description: >-
  Shape a repository so parallel coding agents can change one capability at a
  time behind stable contracts: vertical capability modules, directional
  dependencies, extension over central mutation, and expand-and-contract
  migration. Use when designing repository structure, reviewing architectural
  coupling, or deciding whether a change may broaden its own scope.
---

# Agent-native modular architecture

## Source

ADR-0014, *Agent-native modular software architecture*, merged in
`rmax-ai/architecture#15` (merge commit `6fbba39`). This skill is the parent of
the suite; language layout lives in `python-capability-workspace`,
`typescript-bun-capability-workspace`, and `rust-capability-workspace`, and the
execution lifecycle continues in `affected-polyglot-toolchain`,
`machine-readable-capability-graph`, `change-envelope-planning`,
`agentic-verification-ladder`, and `token-efficient-repository-context`.

## Purpose

Convert architecture from prose intent into a property agents can exploit:
the cheapest safe operation is a small local change behind an explicit
contract, so parallel work intersects as little as possible.

The dominant risk is **semantic interference** — two textually independent
changes that invalidate each other through hidden coupling, unstable
interfaces, shared mutable state, or broad refactors. Treat interference, not
line count, as the thing your structure minimizes.

## When to use

Use this skill when:

- choosing the top-level layout of a new repository;
- a change requires touching several "shared" or "common" files and you need
  to decide whether that is a defect in the structure;
- reviewing a design for coupling, cycles, or an implicit central registry;
- planning a cross-cutting migration that must not become a repository-wide
  refactor;
- deciding whether to split a repository or extract a service.

Do not apply this skill as a mandate to restructure a stable repository for
appearance. Adoption is incremental.

## Required inputs

Collect, or state as unknown:

- `capabilities`: the cohesive slices the system actually owns;
- `consumers`: who calls each capability, and through which surface;
- `contracts`: durable cross-process or cross-language schemas, if any;
- `hot_files`: paths that unrelated features currently must edit;
- `dependency_edges`: known directional relationships, including cycles;
- `stability`: which repositories or modules are stable versus in flight.

## Procedure

### 1. Cut the repository by vertical capability

The default architectural unit is a **capability module** that owns its domain
behavior, application logic, ports, adapters, persistence concerns, tests, and
observability for that capability.

Prefer `cohort-discovery/`, `cohort-specification/`, `cohort-fulfillment/`
over `controllers/`, `services/`, `repositories/`, `models/`, `utils/`.
Horizontal layering may exist *inside* a capability; it must not force
unrelated capabilities to edit the same files.

### 2. Make each capability own its internals and state

A capability exposes stable public entry points. Others must not deep-import
its private implementation, read or write its persistence tables directly,
depend on private classes or internal directory structure, or mutate its
configuration behind its API. Cross-capability behavior goes through explicit
interfaces: typed APIs, events, commands, schemas, or declared library entry
points.

### 3. Keep dependencies directional and inspectable

Dependencies should form a directed graph that is acyclic where practical.
Cycles are architectural debt and require an explicit, recorded exception.
A shared abstraction is allowed when it is a genuinely stable cross-cutting
contract, not merely convenient code reuse.

### 4. Prefer stable contracts over shared implementation

Cross-process or cross-language boundaries use explicit versioned contracts:
Protocol Buffers by default for durable polyglot service and event contracts
where generated bindings help; JSON/HTTP schemas where ecosystem constraints
make them preferable. In-process same-language boundaries may use native
interfaces and types. Contract changes are higher risk than implementation
changes and belong to `change-envelope-planning` (ADR-0020), not to this
skill's local-edit path.

### 5. Prefer extension over central mutation

Adding a provider should be additive — a new adapter directory next to
`exa/`, `deepseek/`, `brave/` — not a new branch in a central `if/else`, route
file, plugin table, or package index. Where discovery is needed, prefer
package/workspace metadata, one manifest per capability, generated registries,
or explicit dependency injection. A hand-edited global registry is not a normal
extension point.

### 6. Minimize shared hot files

Identify files every feature must touch: monolithic route registries, central
plugin maps, giant config files, umbrella exports, shared constants modules.
They are contention points and merge-conflict magnets. When a central aggregate
is genuinely necessary, generate it deterministically from local declarations
and fail verification when it drifts.

### 7. Choose modular repositories over premature microservices

Runtime isolation and source modularity are separate concerns. The default is
one repository containing strongly bounded projects or modules, with explicit
package and service boundaries, and independent deployability only where
operational need justifies it. A module may later become a service without
changing its logical contract. Do not create network boundaries to obtain
source-ownership boundaries.

### 8. Evolve through compatibility, not broad rewrites

Cross-cutting migrations use **expand-and-contract**:

1. introduce the new contract or abstraction;
2. provide a compatibility adapter;
3. migrate consumers independently;
4. measure remaining old-path usage;
5. remove the compatibility layer in a separately verified change.

Agents must not perform speculative repository-wide refactors when a
compatibility seam localizes the transition.

### 9. Make the important rules machine-checkable

`AGENTS.md` prose is guidance, not enforcement. Durable constraints should
eventually be enforced by repository metadata, dependency rules, static checks,
contract tests, or the orchestration control plane. Metadata lives in
`machine-readable-capability-graph` (ADR-0019), change classes in
`change-envelope-planning` (ADR-0020), and gate selection in
`agentic-verification-ladder` (ADR-0021).

### 10. Apply proportionate ceremony

A small repository gets the principles, not the scaffolding. One cohesive
package, one crate, or one single-package workspace is often the correct
answer; empty layers and speculative boundaries are their own maintenance
cost.

## Invariants

- A capability owns its behavior, state, tests, and adapters.
- Cross-capability calls pass through a declared public surface.
- The dependency graph is directed, mostly acyclic, and inspectable.
- Contracts are explicit and versioned; implementations are replaceable.
- Adding an implementation is additive rather than a central edit.
- No file is edited by every feature without a generation step.
- Source modularity is not conflated with runtime isolation.
- Structure changes arrive as compatible transitions, not rewrites.

## Anti-patterns

**Wrong:** a `common/` package that every module imports and anyone may add to.
**Right:** named libraries with real consumers, or a capability-local helper.

**Wrong:** a provider registry file that each new provider must edit.
**Right:** per-provider adapters plus generated or manifest-driven discovery.

**Wrong:** importing `pkg.adapters.sql.internal.query_builder` from another
package because the function was handy.
**Right:** call the documented entry point in `pkg.api`, and widen that surface
deliberately if it is insufficient.

**Wrong:** extracting four services from one codebase to separate teams' code.
**Right:** keep one deployable, split modules, and extract a service only when
runtime scaling, failure isolation, or release cadence requires it.

**Wrong:** a repository-wide rename or directory shuffle in the same change as
a feature.
**Right:** land the seam and adapter, migrate callers separately, delete the
old path when usage reaches zero.

## Verification checklist

- [ ] Every changed path belongs to exactly one owning capability.
- [ ] No new import crosses into another capability's private modules.
- [ ] No new edge creates a dependency cycle; an exception is recorded if it does.
- [ ] Contract changes are absent, or are classified above L1 and planned.
- [ ] The change adds no new edit to a central registry or umbrella export.
- [ ] New implementations are additive: a new file plus local wiring.
- [ ] Any compatibility layer has a dated removal condition.
- [ ] Enforceable rules are covered by a check, or are explicitly listed as
      not yet enforced.

## Failure and escalation

Stop and escalate, rather than improvising, when:

- completion requires editing another capability's private internals;
- the requested change silently becomes a contract or boundary change;
- a cycle is unavoidable without deciding which module owns the behavior;
- the repository is stable and the change is structural rather than behavioral;
- two capabilities claim the same source path and ownership is ambiguous.

Treat each of these as a re-plan event with a durable record, not as a reason
to widen the patch.

## Handoffs

- `python-capability-workspace`, `typescript-bun-capability-workspace`,
  `rust-capability-workspace` — concrete layout for one language.
- `affected-polyglot-toolchain` — project graph, canonical tasks, affected runs.
- `machine-readable-capability-graph` — ownership and contract metadata.
- `change-envelope-planning` — change class and allowed mutation surface.
- `agentic-verification-ladder` — which gates a change must pass.
- `token-efficient-repository-context` — how an agent finds all of the above cheaply.

## Compact example

Task: add a new search provider. Under this architecture the change adds
`packages/search/src/.../adapters/<provider>.py`, a provider-specific test, and
one wiring line at the application composition root. It does not edit any other
package, any central provider switch, or the search core. If the provider needs
a new field on the public search contract, the work splits: a contract change
(higher class, reviewed) followed by an additive adapter change.
