---
name: change-envelope-planning
description: >-
  Classify a planned change as L0-L3, resolve it to an immutable envelope of
  modules and allowed paths, and schedule parallel work by mutation overlap.
  Use before dispatching an agent, when a task starts to broaden, or when
  deciding whether two changes may run concurrently.
---

# Change envelope planning

## Source

ADR-0020, *Change envelopes, architectural change classes, and optimistic agent
integration*, merged in `rmax-ai/architecture#15` (merge commit `6fbba39`).
Related: ADR-0008, ADR-0009, ADR-0010, ADR-0014, ADR-0019.

## Purpose

Decide mutation scope and semantic risk before work starts, so parallel agents
cannot make incompatible assumptions or quietly turn a local task into an
architectural refactor. Git isolates text; an envelope isolates semantics.

The envelope extends the existing durable task contract rather than inventing a
second orchestration mechanism: the control plane owns the schema, this skill
owns the semantics.

## When to use

Use this skill when:

- turning a plan into a dispatchable task;
- deciding whether two tasks may run in parallel;
- an agent reports that finishing requires more than it was given;
- reviewing a PR whose diff is larger than its stated intent;
- sequencing a contract, dependency, or toolchain change.

## Required inputs

Collect, or state as unknown:

- `intent`: one sentence describing the end state;
- `work_item`: the durable issue or task reference;
- `base_revision`: the exact commit the work starts from;
- `modules`: the owning module(s) and what they read;
- `mutation_surface`: paths expected to change;
- `contracts` and `dependencies`: whether either may change;
- `acceptance`: externally meaningful outcomes;
- `parallel_neighbours`: other in-flight work in the same repository.

## Procedure

### 1. Classify the change

```text
L0  local implementation
    Private implementation change inside one module; no public contract change.

L1  module-compatible change
    Changes one module/public implementation while preserving declared external contracts.

L2  contract/dependency/toolchain change
    Changes a public contract, dependency edge, schema, workspace/lock/toolchain state,
    persistence contract, or multiple ownership boundaries.

L3  architecture/system change
    Changes module boundaries, ownership, lifecycle semantics, control-plane invariants,
    cross-repository architecture, or introduces/removes major infrastructure.
```

The level describes semantic blast radius, not lines changed. A one-line schema
edit can be L2; a large private refactor inside one module can be L0.

### 2. Resolve an immutable envelope

```yaml
schema_version: 1
work_item: rmax-ai/delegation-queue#NNN
base_revision: <git-sha>
change_class: L1
intent: add-deepseek-search-adapter

modules:
  owns:
    - search
  reads:
    - search-contracts

allowed_paths:
  - packages/search/**
forbidden_paths:
  - .moon/**
  - .prototools
  - bun.lock
  - uv.lock
  - Cargo.lock

contracts:
  may_change: false

dependencies:
  may_change: false

acceptance:
  - search contract suite passes
  - provider behavior tests pass

verification_profile: module-compatible
```

Freeze it before dispatch. A changed envelope is a re-plan event with a new
revision, not an edit to the running task's brief.

### 3. Enforce before submission and after execution

Pre-submit checks:

- target repository and base revision exist;
- module and path ownership resolve through capability-graph metadata;
- allowed and forbidden paths are coherent (no path in both);
- the declared class permits the requested contract or dependency mutations;
- an acceptance and verification profile is present;
- concurrent envelopes do not overlap unsafely.

Post-execution checks compare the actual changed files, and any detected
contract or dependency change, against the approved envelope.

### 4. Stop on scope expansion

If completion requires another capability's private files, an undeclared
contract change, lock/toolchain/workspace changes, a persistence migration
outside the envelope, or a repository-wide refactor, the agent stops or returns
a structured re-plan request. It must not silently broaden the patch.

Generated files are allowed only when the generator or schema change is inside
the envelope and generation is declared.

### 5. Treat architectural change as exceptional

L0 and L1 should be the majority of autonomous work. L2 requires explicit impact
analysis of consumers and broader verification. L3 requires architectural review
and, where cross-system, an ADR or an explicit statement that an existing ADR
already authorizes the change.

An agent's preference for a cleaner abstraction is not a reason to upgrade a
local task.

### 6. Schedule by overlap, not by optimism

The planner compares:

```text
path overlap
+ capability ownership overlap
+ contract producer/consumer overlap
+ dependency graph edges
+ shared lock/toolchain surfaces
```

Two L0/L1 tasks in independent modules normally run in parallel. Two tasks that
change a shared contract, lockfile, generated registry source, or architecture
root normally serialize or are explicitly ordered.

### 7. Isolate every attempt

Each attempt receives an immutable base revision, an isolated worktree or
workspace, the resolved envelope, only the context the task needs, and its own
verification output. Concurrent agents never share a mutable checkout.
ADR-0010 remains authoritative for ephemeral workspace and cache
infrastructure.

### 8. Integrate optimistically

```text
independent implementation
  -> local/affected verification
  -> review
  -> update/rebase against current integration head
  -> recompute affected/semantic impact
  -> reverify required gates
  -> merge
```

Agents do not message one another merely because they share a repository.
Direct coordination is reserved for genuine contract or ordering dependencies
that cannot be represented in the issue and plan graph.

### 9. Handle stale bases deterministically

Before merge, compare the task base revision with the current integration head.
If intervening changes touch the same module, a consumed or produced contract,
a dependency edge, or shared workspace/toolchain state, recompute the envelope
impact and the required verification. A clean textual rebase is not evidence of
semantic safety.

### 10. Keep state in durable records

The envelope is durable task state, not chat convention. Issues, pull requests,
and control-plane records remain authoritative for intent, dependencies,
approvals, the actual patch, verification evidence, and terminal state. Chat is
for wake-up and coordination only.

### 11. Decompose refactors with expand-and-contract

```text
new interface/contract
  -> compatibility adapter
  -> independent consumer migrations
  -> observed old-path usage reaches zero
  -> removal task
```

Give each consumer migration its own L0/L1 envelope where possible; this turns a
high-conflict global refactor into parallel low-conflict work.

## Invariants

- Every dispatched task has a class and an envelope before submission.
- The envelope is immutable once dispatched; changes are re-plans.
- Class reflects semantic blast radius, not diff size.
- Allowed and forbidden paths never overlap.
- Contract, dependency, and lockfile mutations require L2 or higher.
- Parallel scheduling is decided by overlap, not by wishful independence.
- Attempts never share a mutable checkout.
- Rebase without impact recomputation is not integration evidence.

## Anti-patterns

**Wrong:** "while I was in there, I also renamed the package and bumped the
lockfile."
**Right:** stop, return a re-plan request naming the second change.

**Wrong:** two agents editing the same shared contract on separate branches and
reconciling at merge.
**Right:** the contract change is one task; consumer tasks follow it.

**Wrong:** an envelope of `allowed_paths: ["**"]` for a bounded feature.
**Right:** the owning module's paths, with the shared surfaces forbidden.

**Wrong:** treating a rebase onto a moved head as proof the change is still safe.
**Right:** recompute affected modules and rerun the required gates.

## Verification checklist

- [ ] The task states a change class with a one-line justification.
- [ ] The envelope names owning modules, allowed paths, forbidden paths.
- [ ] `contracts.may_change` and `dependencies.may_change` match the class.
- [ ] Acceptance criteria are externally observable.
- [ ] No concurrent envelope overlaps this one unsafely.
- [ ] The actual diff stays inside `allowed_paths` and outside `forbidden_paths`.
- [ ] No lockfile, toolchain, or generated-registry edit appeared unannounced.
- [ ] After any rebase, affected scope and gates were recomputed.

## Failure and escalation

Escalate when:

- ownership of a required path cannot be resolved;
- the task cannot complete inside its envelope;
- the class boundary is contested (L1 versus L2 for a contract-adjacent change);
- an L3 change lacks an ADR or explicit prior authorization;
- overlap detection is impossible because envelopes are missing.

Each of these is a durable re-plan, not a reason to widen scope silently.

## Handoffs

- `machine-readable-capability-graph` — resolves ownership and contract edges.
- `agent-native-modular-architecture` — for deciding whether the boundary
  itself is wrong (an L3 decision).
- `affected-polyglot-toolchain` — maps envelope to affected projects and tasks.
- `agentic-verification-ladder` — turns class into required gates.
- `token-efficient-repository-context` — supplies only in-envelope context.

## Compact example

Two tasks are queued: (a) add an Exa adapter under `packages/search/**`, class
L1; (b) add a field to `search.v1.SearchService`, class L2. They overlap on the
`search` module and on a contract, so (b) is sequenced first and (a) rebases
afterwards. A third task touching an unrelated `analytics` module runs in
parallel with both.
