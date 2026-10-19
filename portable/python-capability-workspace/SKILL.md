---
name: python-capability-workspace
description: >-
  Lay out Python repositories developed by agents: one uv workspace with one
  project per capability, src/ layouts, narrow public entry points, ports and
  adapters, and behavior-oriented tests. Use when creating a Python repository,
  splitting a package, or deciding where a new module and its tests belong.
---

# Python capability workspace

## Source

ADR-0015, *Python capability and workspace layout for agent-developed systems*,
merged in `rmax-ai/architecture#15` (merge commit `6fbba39`). Parent decision:
`agent-native-modular-architecture`. Boundary validation stays with ADR-0011
and the `pydantic-boundary-validation` skill.

## Purpose

Give every Python capability an obvious ownership and verification boundary
while keeping the toolchain idiomatic: one uv workspace, one lockfile, one
package per independently owned capability, and import surfaces that make
accidental coupling visible.

## When to use

Use this skill when:

- creating a Python repository or a Python project inside a polyglot repository;
- a repository has multiple import roots, ad-hoc scripts, or a shared
  `utils.py` that everything imports;
- deciding whether a new concern is a package, a module, or an adapter;
- a task needs to know where its tests belong and how to verify only itself;
- reviewing a Python change for boundary or import-direction violations.

## Required inputs

Collect, or state as unknown:

- `capabilities`: the cohesive slices and their expected consumers;
- `deployables`: entry points that must be runnable (API, worker, CLI);
- `dependencies`: external runtime dependencies per capability;
- `boundaries`: data that crosses a trust boundary (request bodies, config,
  queue envelopes, database rows);
- `verification`: the commands the project can already run;
- `existing_layout`: whether the repository is single-project or multi-project.

## Procedure

### 1. Choose single-project or workspace layout deliberately

Multi-project repository:

```text
repo/
  pyproject.toml              # uv workspace root
  uv.lock
  apps/
    api/
      pyproject.toml
      src/rmax_api/
      tests/
  packages/
    cohort_discovery/
      pyproject.toml
      src/rmax_cohort_discovery/
      tests/
    cohort_contracts/
      pyproject.toml
      src/rmax_cohort_contracts/
      tests/
```

Use `apps/` for deployable or entry-point projects and `packages/` for
capability libraries, adapters, and contract libraries. A single-project
repository keeps `pyproject.toml`, `src/<package>/`, `tests/`. Do not create a
workspace for architectural appearance.

### 2. Let uv own membership and the lockfile

The root `pyproject.toml` declares membership and the repository shares one
`uv.lock`:

```toml
[tool.uv.workspace]
members = ["apps/*", "packages/*"]
```

Each member keeps its own `pyproject.toml` and declares its own direct
dependencies; cross-workspace dependencies are explicit. The lockfile is
repository-level build state, not a feature-owned file — dependency updates
therefore carry a broader change class than ordinary source edits.

### 3. Always use `src/` layouts for packaged projects

Use `src/<import_name>/` rather than importing from the repository root. This
removes accidental import-path coupling and makes the package behave like the
installed artifact.

### 4. Structure inside a capability by stable responsibility

```text
src/rmax_cohort_discovery/
  __init__.py
  api.py                 # intentionally small public surface
  domain/
  application/
  ports/
  adapters/
```

- `domain/` — values, invariants, deterministic rules;
- `application/` — use cases and orchestration inside the capability;
- `ports/` — Protocols/interfaces required from the outside world;
- `adapters/` — HTTP, DB, provider, filesystem, queue, framework code;
- `api.py` — the narrow surface other projects may import.

Small capabilities collapse directories. The invariant is dependency
direction, not folder count.

### 5. Keep frameworks and infrastructure at the edge

Domain and application code must not require FastAPI, SQLAlchemy, provider
SDKs, CLI frameworks, or transport-specific types unless that dependency is
part of the domain itself. Prefer ports plus adapters so an integration can be
replaced without rewriting core behavior.

### 6. Validate at serialized boundaries only

ADR-0011 remains authoritative: Pydantic v2 at non-trivial serialized or
untrusted boundaries; internal trusted objects may use dataclasses, enums,
Protocols, TypedDicts, or ordinary typed classes. Authorization, workflow
transitions, and business policy stay deterministic domain logic. Do not create
a model for every internal object for consistency's sake. See
`pydantic-boundary-validation` for the boundary mechanics.

### 7. Expose a narrow public surface and prove it

Other projects import documented public modules:

```python
from rmax_cohort_discovery.api import discover
```

not `rmax_cohort_discovery.adapters.sql.internal.query_builder`. Use private
modules, `__all__`, static dependency checks, or packaging boundaries; do not
rely on naming convention alone for a critical boundary.

### 8. Place tests by behavior and contract

```text
tests/
  contract/
  behavior/
  integration/
  fixtures/
```

Verify public behavior, domain invariants, serialization contracts, and adapter
integration. Avoid tests that encode the current internal structure. A feature
should normally be verifiable from its own package before repository-wide
verification is required. Gate selection follows
`agentic-verification-ladder`.

### 9. Expose the canonical task names

Where meaningful, the project provides Moon tasks equivalent to:

```text
fmt       -> ruff format --check
lint      -> ruff check
check     -> static/type checks applicable to the project
test      -> pytest
build     -> package/build validation when distributable
contract  -> contract/schema compatibility checks when applicable
```

Exact commands stay project-owned; the vocabulary is fixed by ADR-0018, so see
`affected-polyglot-toolchain` before inventing task names.

### 10. Refuse utility sinks and import-time registration

Do not create `utils.py`, `helpers.py`, or `common/` as the default destination
for reusable code. Reusable code belongs inside the capability that owns its
semantics, in a deliberately named small library with explicit consumers, or in
a stable cross-cutting package justified by multiple real consumers. Prefer
explicit composition — construct providers in the composition root — over
global registries populated by import side effects.

## Invariants

- One package per independently owned capability; one shared `uv.lock`.
- Packaged code lives under `src/`, not the repository root.
- Dependencies point inward: adapters depend on ports, never the reverse.
- The public surface is small, documented, and separately checkable.
- Boundary validation is Pydantic at untrusted edges only.
- Tests assert behavior and contracts, not implementation shape.
- Providers and plugins are composed explicitly, not registered at import.

## Anti-patterns

**Wrong:** `repo/utils.py` accumulating date helpers, retry logic, and one
capability's business rule.
**Right:** the rule lives in its capability; genuinely shared helpers become a
named library with listed consumers.

**Wrong:** `from rmax_api.adapters.db import session` in another package to get
a session cheaply.
**Right:** depend on the capability's declared API, or declare a dependency on
a shared infrastructure package.

**Wrong:** adding `pydantic.BaseModel` to an internal value object that never
crosses a boundary.
**Right:** a frozen dataclass or enum, with validation only at the edge.

**Wrong:** a `providers/__init__.py` that imports every adapter so a registry
dict gets populated.
**Right:** the application composition root constructs the adapters it uses.

**Wrong:** one flat `tests/test_everything.py` shared by all packages.
**Right:** package-local `behavior/` and `contract/` suites owned by the package.

## Verification checklist

- [ ] New code lives in the owning package under `src/`.
- [ ] The package declares every dependency it imports.
- [ ] No import escapes a package root into another package's internals.
- [ ] `api.py` (or equivalent) exposes the new behavior, or the surface change
      is called out explicitly.
- [ ] Domain/application code imports no framework or provider SDK.
- [ ] Boundary inputs are validated with Pydantic; internal objects are not.
- [ ] Tests target public behavior, invariants, or contracts.
- [ ] `fmt`, `lint`, `check`, `test` pass for the owning project alone.

## Failure and escalation

Escalate when:

- the capability boundary is unclear and two packages both plausibly own a path;
- the change requires a dependency the domain cannot accept;
- a shared library is proposed without multiple real consumers;
- a dependency update is required but the task's envelope forbids lockfile
  changes — return a re-plan request instead of editing the lock.

## Handoffs

- `agent-native-modular-architecture` — why the boundaries exist.
- `pydantic-boundary-validation` — validation and domain error codes.
- `affected-polyglot-toolchain` — Moon tasks and affected execution.
- `machine-readable-capability-graph` — `module.yaml` for the new package.
- `agentic-verification-ladder` — required gates.

## Compact example

Adding provider `deepseek` to a search package touches
`packages/search/src/rmax_search/adapters/deepseek.py`, a contract test under
`packages/search/tests/contract/`, and the app composition root. It adds no
`utils.py`, edits no other package, and does not touch `uv.lock` unless a new
dependency is genuinely introduced.
