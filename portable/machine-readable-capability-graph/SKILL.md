---
name: machine-readable-capability-graph
description: >-
  Declare ownership, public entry points, contracts, dependencies, risk, and
  verification per module in a local manifest, compiled into a queryable graph
  instead of a hand-edited central registry. Use when a planner needs to know
  what a path owns, what depends on it, or what a schema change affects.
---

# Machine-readable capability graph

## Source

ADR-0019, *Machine-readable capability ownership and dependency graph*, merged
in `rmax-ai/architecture#15` (merge commit `6fbba39`). Related: ADR-0005,
ADR-0008, ADR-0014, ADR-0018, ADR-0020, ADR-0022.

## Purpose

Answer planning questions from declarative metadata instead of from source
archaeology: which capability owns this path, what does it expose, what does it
depend on, what depends on it, which contracts does it produce or consume, how
is it verified, and what change class applies.

Moon and language package managers describe structural dependencies. They do
not express semantic ownership, contract production and consumption, risk, or
intended public entry points. This skill adds exactly that layer — and nothing
that can be derived.

## When to use

Use this skill when:

- a repository has more than one independently owned project;
- a planner must scope a change before reading implementation;
- a schema or public-API change needs impact analysis;
- ownership of a path is disputed or overlapping;
- a repository root catalog or registry has become a manual bottleneck.

Do not require this metadata for a trivial single-project repository when Moon
and package manifests already answer the question.

## Required inputs

Collect, or state as unknown:

- `projects`: module ids, kinds, and owners;
- `entrypoints`: the public modules each module exposes;
- `contracts`: produced and consumed contract identifiers;
- `dependencies`: semantic dependency edges, separate from package edges;
- `risk`: the default change class per module;
- `verification`: fast and contract task names per module;
- `shared_surfaces`: paths intentionally shared (lockfiles, schemas, policy).

## Procedure

### 1. Add one local manifest per non-trivial project

```yaml
schema_version: 1
id: search
kind: capability
language: python
owner: search

public_entrypoints:
  - rmax_search.api

contracts:
  produces:
    - search.v1.SearchService
  consumes:
    - identity.v1.Actor

dependencies:
  semantic:
    - identity

risk:
  default_change_class: L1

verification:
  fast:
    - lint
    - check
    - test
  contract:
    - contract
```

The file lives in the project root next to the language manifest
(`pyproject.toml`, `package.json`, `Cargo.toml`).

### 2. Keep the manifest authoritative only for semantic metadata

Derive structural facts rather than restating them:

- project path and task graph from Moon;
- Python dependencies from project metadata and uv;
- TypeScript dependencies from package manifests and Bun;
- Rust dependencies from Cargo metadata;
- protobuf relationships from Buf descriptors and configuration.

`module.yaml` must not become a second package manager, and must not duplicate a
fact the language manifest already states without a recorded reason.

### 3. Compile local declarations into one generated graph

```text
Moon project graph
+ language package metadata
+ module.yaml semantic metadata
+ contract descriptors
= architecture graph
```

Emit JSON, SQLite, Graphviz/Mermaid, or another queryable form. Generated
aggregate state is never hand-edited.

### 4. Make the graph answer planning questions cheaply

At minimum:

```text
What capability owns this path?
What public API does it expose?
What does it depend on?
What depends on it?
What contracts does it produce/consume?
What verification tasks certify it?
What default change class applies?
Which modules are affected by this change?
```

Agents consult the graph before broad source exploration — this is the entry
point that makes `token-efficient-repository-context` work.

### 5. Keep path ownership unambiguous

Source paths map to exactly one owning project, except explicitly shared
repository-level files such as lockfiles, root build configuration, schemas, and
policy. Overlapping ownership is invalid unless the overlap is a documented
shared surface.

### 6. Distinguish public entry points from implementation

Record the intended surface, and enforce it with the language mechanism that
fits: package `exports` in TypeScript, package and module boundary rules in
Python, crate visibility in Rust, service and message descriptors for wire
contracts. An agent should not need to read internals to learn how a module is
meant to be used.

### 7. Record contract production and consumption as first-class edges

When a module exposes or consumes a durable contract, record the relation in
metadata or derive it from generated protocol metadata. This is what makes
impact analysis possible before a schema change lands.

### 8. Never maintain a hand-edited root module registry

A root catalog may exist for tooling or documentation, but it is generated from
project-local manifests and verification fails when generation is stale.

### 9. Validate the graph as part of verification

Catch at least:

- duplicate module ids;
- paths with conflicting owners;
- references to missing modules or contracts;
- undeclared dependency edges detectable from package or import metadata;
- prohibited dependency cycles;
- verification task names that no project task provides;
- stale committed graph artifacts.

### 10. Keep cross-repository aggregation read-only

An estate-level index may aggregate repository graphs, but source-of-truth
metadata stays repository-local. Feature development must never depend on a
central writable architecture service.

## Invariants

- One manifest per independently owned project; one owner per path.
- Semantic metadata is declared locally, never centrally.
- Structural facts are derived, not duplicated.
- The graph is generated; its inputs are reviewed.
- Public entry points are distinguishable from implementation.
- Contract edges exist for every durable contract in use.
- Graph validation is part of verification, not a documentation chore.

## Anti-patterns

**Wrong:** a root `modules.yaml` listing every module, edited by every new
module's author.
**Right:** per-project `module.yaml` files plus a generated root catalog.

**Wrong:** restating `[project].dependencies` inside `module.yaml`.
**Right:** let uv own dependencies; record only semantic edges.

**Wrong:** marking every module `public_entrypoints: [<package>]` so the field
stops meaning anything.
**Right:** name the one or two modules consumers may import.

**Wrong:** discovering a contract consumer by searching the codebase during a
schema change.
**Right:** query consumed-contract edges, then confirm in code.

## Verification checklist

- [ ] Every changed path resolves to exactly one owning module.
- [ ] The owning module's `module.yaml` was created or updated.
- [ ] Declared entry points match what consumers actually import.
- [ ] Contract produce/consume edges are present for changed contracts.
- [ ] `id` values are unique; ownership paths do not overlap.
- [ ] Referenced verification tasks exist in the project.
- [ ] The generated graph was regenerated and is not stale.
- [ ] No root registry gained a hand-written entry.

## Failure and escalation

Escalate when:

- two modules legitimately claim the same path and the split is unclear;
- a module's public entry point does not exist in the language manifest;
- a contract is consumed but the producer is unknown;
- validation requires metadata the repository cannot supply (record the gap
  rather than inventing facts);
- a planner wants the central index to become writable.

## Handoffs

- `agent-native-modular-architecture` — the boundaries being described.
- `affected-polyglot-toolchain` — structural project/task graph to merge with.
- `change-envelope-planning` — envelopes resolve ownership through this graph.
- `agentic-verification-ladder` — verification tasks referenced by manifests.
- `token-efficient-repository-context` — graph-first context construction.

## Compact example

Before touching `search.v1.SearchService`, an agent queries the graph: producer
`search`, consumers `api` and `analytics`, default class `L1` on the producer.
Because a consumer edge exists across a contract, the planned change is not a
local edit; it becomes a contract change with impact analysis, and only then
does the agent open any implementation file.
