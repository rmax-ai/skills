---
name: rust-capability-workspace
description: >-
  Lay out Rust repositories as Cargo workspaces where crates map to ownership:
  small public surfaces, explicit dependency direction, adapter crates for
  volatile integrations, and crate-local verification. Use when creating a
  workspace, adding a crate or provider, or reviewing visibility and feature-flag
  design.
---

# Rust capability workspace

## Source

ADR-0017, *Rust crate and workspace layout for agent-developed systems*, merged
in `rmax-ai/architecture#15` (merge commit `6fbba39`). Parent decision:
`agent-native-modular-architecture`.

## Purpose

Map crate boundaries to semantic ownership so an agent can modify and verify a
small region independently. Cargo already enforces visibility and dependency
rules; the design work is choosing crates that express ownership instead of
convenience, and keeping volatile integrations out of stable cores.

## When to use

Use this skill when:

- creating a Rust repository or a Rust project inside a polyglot repository;
- deciding whether a module should become a crate or stay a module;
- adding a provider or integration adapter;
- an oversized `core` or `utils` crate is accumulating unrelated behavior;
- reviewing a feature-flag matrix or public API surface.

## Required inputs

Collect, or state as unknown:

- `capabilities`: cohesive slices and the traits/APIs they expose;
- `deployables`: binaries and their composition roots;
- `integrations`: provider or infrastructure implementations and their churn;
- `contracts`: protobuf or wire schemas, if any;
- `features`: genuinely optional compile-time capabilities;
- `verification`: existing `fmt`, `check`, `lint`, `test`, `build` commands.

## Procedure

### 1. Use the Cargo workspace as the project graph

```text
repo/
  Cargo.toml
  Cargo.lock
  apps/
    gateway/
      Cargo.toml
      src/
  crates/
    search/
      Cargo.toml
      src/
      tests/
    search-exa/
      Cargo.toml
      src/
      tests/
    search-deepseek/
      Cargo.toml
      src/
      tests/
    contracts/
      Cargo.toml
      src/
      tests/
```

A small repository with one cohesive crate stays one crate. The root workspace
uses `members`, `workspace.dependencies`, `workspace.lints`, and shared package
metadata where they reduce drift without hiding direct dependency ownership.

### 2. Choose crates that represent ownership

A crate should be one of: a domain/capability core, a specific adapter or
integration, a deployable binary, a deliberately stable contract library, or a
small cross-cutting primitive with multiple real consumers. Avoid a giant
`core` crate that accumulates unrelated behavior and a broad `utils` crate that
becomes a dependency hub.

### 3. Keep public surfaces small

- implementation modules private by default;
- `pub(crate)` for workspace-internal implementation;
- a small stable API from the crate root or clearly named public modules;
- never make a type public merely to simplify tests.

Consumers depend on crate APIs, not on source-tree structure.

### 4. Keep dependency direction explicit

```text
application binary
      |
      v
  capability API
      |
      v
 domain/application core
      ^
      |
 adapter crates implement ports
```

Adapters may depend on the capability's port definitions. The core must not
depend on a concrete provider SDK unless that SDK is genuinely part of the
capability contract. Cargo forbids cycles; do not simulate one with callbacks
or a service locator that recreates the same coupling invisibly.

### 5. Split volatile integrations from stable cores

```text
crates/search/            # traits, domain, orchestration
crates/search-exa/        # Exa adapter
crates/search-deepseek/   # DeepSeek adapter
```

Split when ownership, dependency, compile time, release, or verification
boundaries justify it. Do not turn every module into a crate.

### 6. Convert at serialized boundaries

Use Serde and generated protocol types as transport representations, not as the
domain model:

```text
wire/generated type
      -> validate/convert
         -> domain type
```

Authorization, workflow transitions, and stateful policy remain explicit domain
logic rather than deserialization side effects.

### 7. Generate protocol bindings, never hand-edit them

Polyglot contracts follow ADR-0018. Generated Rust bindings live in an obvious
generated location or build output and are never manually modified. If
generated source is committed, CI regenerates and fails on drift. See
`affected-polyglot-toolchain` for the Buf workflow.

### 8. Keep feature flags bounded

Cargo features suit genuinely optional compile-time capabilities. They must not
become an alternative architecture for selecting dozens of runtime providers or
hiding incompatible dependency graphs. Prefer runtime composition for
interchangeable providers unless compile-time selection has concrete
operational benefit.

### 9. Expose the canonical verification tasks

```text
fmt       -> cargo fmt --all --check
check     -> cargo check for the affected package/targets
lint      -> cargo clippy for the affected package/targets, warnings denied by policy
test      -> cargo test for the affected package; broader dependents when required
build     -> cargo build for deployable artifacts
contract  -> protocol/schema compatibility checks when applicable
```

`--workspace --all-targets --all-features` belongs to integration or full gates,
not to every local edit.

### 10. Keep tests close to the owning crate

Crate-local unit tests cover deterministic internal invariants; `tests/` covers
public behavior and integration boundaries. Cross-crate system tests live in the
smallest project that owns the system behavior. Avoid a global test crate whose
shared fixtures every feature must modify.

### 11. Compose at application roots

Binaries select concrete adapters and wire them to capability APIs. Avoid
global mutable service registries and registration macros that force every new
provider to edit a central file; prefer explicit constructors or generated
plugin metadata.

## Invariants

- Every crate has one ownership reason to exist.
- Public API is intentional, minimal, and type-checked.
- Adapter crates depend on core traits; cores do not depend on adapters.
- Generated bindings are outputs, not sources.
- Features describe optional compilation, not provider selection.
- Verification runs at crate scope before workspace scope.

## Anti-patterns

**Wrong:** `crates/core` containing search, cohort, billing, and shared types.
**Right:** one crate per capability plus a named contract crate.

**Wrong:** `pub` on a struct so an integration test can construct it directly.
**Right:** a test-only constructor or a public API that the domain actually wants.

**Wrong:** a `providers` cargo feature per provider, producing a 2^N feature
matrix.
**Right:** runtime composition with adapter crates behind a shared trait.

**Wrong:** editing `src/generated/search.v1.rs` to fix a field name.
**Right:** edit the `.proto`, regenerate, and commit the regenerated output.

**Wrong:** one `integration-tests` crate holding every fixture.
**Right:** behavior tests in the owning crate; system tests at the smallest
owning project.

## Verification checklist

- [ ] The new crate has a single ownership reason and a stated owner.
- [ ] Public items are justified; internals remain private or `pub(crate)`.
- [ ] Dependency direction holds; no core-to-adapter edge was added.
- [ ] `cargo check` and `cargo clippy` pass for the affected crate.
- [ ] `cargo test` passes for the affected crate, plus declared dependents.
- [ ] Generated code was regenerated rather than edited.
- [ ] No new feature flag selects a runtime provider.
- [ ] `Cargo.lock` is unchanged, or the change is classified as dependency work.

## Failure and escalation

Escalate when:

- the correct crate boundary is ambiguous between two owners;
- a needed public API would expose an internal type;
- compile-time feature selection is proposed for interchangeable providers;
- the change needs workspace dependency or lockfile edits outside the envelope;
- a dependency cycle appears and no owner can be named.

## Handoffs

- `agent-native-modular-architecture` — capability and contract principles.
- `affected-polyglot-toolchain` — Moon task graph, proto/Buf, generated bindings.
- `machine-readable-capability-graph` — `module.yaml` per crate.
- `change-envelope-planning` — change class for lockfile or feature changes.
- `agentic-verification-ladder` — required gates.

## Compact example

Adding provider `deepseek` to `crates/search` creates
`crates/search-deepseek/` implementing the existing `SearchProvider` trait,
adds its tests, and wires the crate in `apps/gateway/src/main.rs`. The stable
`search` core is untouched, no feature flag is introduced, and no generated
binding is edited.
