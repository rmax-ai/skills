---
name: affected-polyglot-toolchain
description: >-
  Operate one project and task graph across languages with Moon, pinned tools,
  a canonical task vocabulary, affected-only verification, and Buf-managed
  protobuf contracts. Use when setting up a polyglot repository, choosing task
  names, deciding what to run after a change, or migrating a mise-managed repo.
---

# Affected polyglot toolchain

## Source

ADR-0018, *Polyglot repository toolchain with Moon, proto, Buf, and affected
verification*, merged in `rmax-ai/architecture#15` (merge commit `6fbba39`).
Related: ADR-0014 through ADR-0017 as realized by the three language-layout
skills.

## Purpose

Give humans, agents, and CI one machine-readable project/task graph, pinned
tool versions, deterministic command names, and the ability to verify only what
a change actually affects — without inventing a command surface per language.

Two unrelated things share the name "proto": Moonrepo's **proto** version
manager, and **Protocol Buffers** schema files managed by **Buf**. Keep them
distinct in every instruction you write.

## When to use

Use this skill when:

- standing up a new multi-project or polyglot repository;
- deciding which task to run after a change, or what a PR must run;
- choosing between `mise` and `proto` for a repository's tool versions;
- introducing or changing a protobuf contract;
- a cached or affected run looks suspiciously fast;
- a repository takes minutes to verify a one-file change.

## Required inputs

Collect, or state as unknown:

- `projects`: the projects and their roles (app, capability, contract);
- `languages`: Python, TypeScript/Bun, Rust, schema-only;
- `version_manager`: existing `mise` rollout or greenfield;
- `tasks`: existing per-project commands for format, lint, check, test, build;
- `graph_inputs`: files whose change invalidates everything (root config,
  lockfiles, toolchain pins);
- `contracts`: protobuf packages and their consumers;
- `ci`: what the pipeline currently runs and how long it takes.

## Procedure

### 1. Make Moon the repository's project and task graph

Each multi-project repository exposes its graph and canonical tasks through
Moon. Moon owns project discovery, task dependencies, task inputs and outputs,
affected calculation, incremental and local caching, orchestration order, and a
stable command surface for humans, agents, and CI.

Do not create one Moon workspace spanning an entire GitHub organization; the
repository is the workspace boundary.

### 2. Pin tool versions with proto for new Moon-native repositories

New repositories without a validated version manager prefer Moon's proto-backed
toolchain with explicit pins:

```text
moon
python
uv
bun
rust/cargo
buf
language-specific generators
```

Never rely on floating `latest` where reproducible agent and CI execution
matters.

### 3. Preserve the existing mise + Moon rollout

Repositories already adopted under the estate rollout keep `mise` as the
version authority and may use `MOON_TOOLCHAIN_FORCE_GLOBALS=true` with
PATH-provided tools. Migrating such a repository to proto is **not** implied:
it requires an explicit change envelope, clean-environment version parity,
legacy command parity, Moon task parity, CI parity, and a documented rollback.
Do not churn a working toolchain for tidiness.

### 4. Standardize the task vocabulary

Expose the applicable tasks from:

```text
fmt        formatting verification
lint       static linting
check      type/compiler/static correctness checks
test       behavioral tests
build      build/package validation
contract   schema/API compatibility checks
verify     aggregate non-mutating project verification
```

Not every project needs every task; do not add no-op tasks for uniformity.
Repository-level verification may aggregate project tasks, but project-local
tasks stay independently runnable.

### 5. Declare inputs and outputs honestly

Moon caching and affected execution are only trustworthy when tasks declare
meaningful inputs and generated outputs. Do not buy speed by omitting inputs
that can change behavior. Root or global configuration that semantically
affects every project must be modeled as a global input or must invalidate
dependent tasks.

### 6. Make affected verification the default inner loop

```text
changed files
   -> Moon affected graph
   -> affected projects/tasks
   -> required upstream dependencies
   -> selected downstream dependents
   -> verification
```

Useful primitives:

```bash
moon query changed-files
moon query affected --downstream direct
moon query projects --affected --downstream direct
moon run :verify --affected remote --downstream direct
```

Exact flags evolve with Moon; the invariant is that scope is derived from the
declared graph rather than guessed by an agent.

### 7. Keep full verification as a separate safety net

Run broader or full verification when root/global build configuration changes,
workspace or lock or toolchain files change, shared contracts change, dependency
graph metadata changes, the affected graph is uncertain, prior evidence shows
undeclared coupling, or at scheduled/nightly and release gates.

The goal is not "never run everything"; it is to avoid running everything for
every local edit.

### 8. Manage durable contracts with Buf

```text
proto/
  search/v1/search.proto
  cohort/v1/cohort.proto
buf.yaml
buf.gen.yaml
```

Buf is the standard interface:

```bash
buf format
buf lint
buf build
buf breaking --against '.git#branch=main'
buf generate
```

Use versioned package names (`...v1`, `...v2`) and compatibility checks before
accepting a contract change. Do not drive normal protobuf workflows through
bespoke `protoc` shell scripts when Buf can express them declaratively.

### 9. Treat generated code as output

Generated bindings must be recognizable as generated. Agents modify the schema
or generator source, never the output. If generated source is committed,
verification regenerates and fails on unexpected diff; if it is not committed,
build and test tasks generate it reproducibly before consumers run.

### 10. Keep shared coordination surfaces out of feature envelopes

```text
.prototools
.moon/**
uv.lock
bun.lock
Cargo.lock
buf.lock and schema dependency lock state
root package/workspace manifests
```

Ordinary feature work should not modify them unless it genuinely changes
dependencies or tooling. Such a mutation is a broader change class under
`change-envelope-planning`.

### 11. Treat remote caching as a separate decision

Moon local caching is part of this decision. A hosted or shared remote cache
introduces credentials, availability, trust, and cost concerns and needs its own
operational decision. Do not add one because the tool supports it.

## Invariants

- One repository, one Moon workspace, one task vocabulary.
- Tool versions are pinned and reproducible in a clean environment.
- Task inputs and outputs are declared, including global invalidation.
- Verification scope comes from the graph, not from agent intuition.
- Contracts are versioned, linted, and breakage-checked with Buf.
- Generated code is never hand-edited.
- Existing mise repositories are not migrated without full parity evidence.

## Anti-patterns

**Wrong:** "run the full suite, it is only eight minutes" on every one-file
change.
**Right:** affected verification in the inner loop, with full runs at gates.

**Wrong:** a task declaring `inputs: ["src/**"]` while reading a root config it
forgot to list.
**Right:** declare the root config as a global input so caching stays honest.

**Wrong:** a `scripts/gen-proto.sh` that calls `protoc` with hand-maintained
flags per language.
**Right:** `buf.yaml` + `buf.gen.yaml` + `buf generate`, plus `buf breaking`.

**Wrong:** switching a working mise repository to proto inside a feature PR.
**Right:** keep mise, and treat any migration as its own enveloped change with
parity and rollback evidence.

**Wrong:** committing generated bindings and editing them when a field changes.
**Right:** edit the `.proto`, regenerate, and let drift detection prove parity.

## Verification checklist

- [ ] Every project declares the applicable canonical tasks.
- [ ] The changed-file set maps to an explicit affected project/task list.
- [ ] Any global input touched by the change forces the broader scope.
- [ ] `moon run :verify --affected` succeeds for the change.
- [ ] Contract changes ran `buf lint`, `buf build`, and `buf breaking`.
- [ ] Generated output matches regeneration (no hand edits).
- [ ] Lockfiles and toolchain pins are unchanged, or classified as dependency
      work.
- [ ] The claim "only affected projects ran" is backed by command output.

## Failure and escalation

Escalate when:

- the affected graph omits a project that the change demonstrably affects
  (undeclared coupling — record it, do not silently run everything);
- a task cannot declare its inputs truthfully;
- a toolchain migration is requested inside a feature task;
- `buf breaking` reports an incompatible change without an agreed version bump;
- a remote cache is proposed without an operational decision.

## Handoffs

- `agent-native-modular-architecture` — the boundaries the graph encodes.
- `python-capability-workspace`, `typescript-bun-capability-workspace`,
  `rust-capability-workspace` — per-language tasks and layout.
- `machine-readable-capability-graph` — semantic metadata Moon cannot derive.
- `change-envelope-planning` — class for lockfile and toolchain edits.
- `agentic-verification-ladder` — how affected scope maps to V0–V5 gates.

## Compact example

A change touches `packages/search/src/adapters/exa.py`. `moon query
changed-files` lists it; `moon query affected --downstream direct` returns
`search` and the `api` app that depends on it. `moon run :verify --affected
--downstream direct` runs lint, check, test for both and skips the unrelated
data pipeline. A one-line edit to `pyproject.toml` in the same change instead
forces the repository-wide verification path.
