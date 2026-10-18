---
name: typescript-bun-capability-workspace
description: >-
  Lay out TypeScript repositories on Bun: workspaces as capability boundaries,
  isolated installs, explicit package exports, package-local tests, and a thin
  root package. Use when creating a Bun workspace, adding a package, migrating
  away from phantom hoisted dependencies, or reviewing deep imports.
---

# TypeScript and Bun capability workspace

## Source

ADR-0016, *TypeScript and Bun capability/workspace layout for agent-developed
systems*, merged in `rmax-ai/architecture#15` (merge commit `6fbba39`). Parent
decision: `agent-native-modular-architecture`. Boundary validation stays with
ADR-0011 and the `zod-boundary-validation` skill.

## Purpose

Make each Bun workspace package a real ownership and verification boundary.
The failure this prevents is nominal packaging: directories that look separate
while runtime dependencies stay hoisted, `exports` stay absent, and packages
deep-import one another's implementation.

## When to use

Use this skill when:

- creating a TypeScript repository or a TypeScript project in a polyglot repo;
- adding a workspace package or a provider adapter;
- a build works locally only because an undeclared dependency was hoisted;
- a central `index.ts` has become a registry every feature must edit;
- reviewing imports, exports, or root configuration spread.

## Required inputs

Collect, or state as unknown:

- `capabilities`: cohesive slices plus their consumers;
- `deployables`: runtime entry points (API, gateway, worker);
- `package_manager`: Bun version and whether isolated installs are already on;
- `dependencies`: foundational packages that might deserve a catalog entry;
- `boundaries`: untrusted payloads that need Zod validation;
- `verification`: existing scripts for format, lint, type check, test, build.

## Procedure

### 1. Use workspaces as capability boundaries

```text
repo/
  package.json
  bun.lock
  bunfig.toml
  apps/
    api/
      package.json
      src/
      tests/
  packages/
    search/
      package.json
      src/
      tests/
    contracts/
      package.json
      src/
      tests/
```

`apps/` holds deployable/entry-point projects; `packages/` holds capabilities,
adapters, contract libraries, and shared domain libraries with explicit
ownership. A small single-package repository stays a single package.

### 2. Keep the root package orchestration-only

The root `package.json` is private and owns workspace configuration, optional
dependency catalogs, and repository-level scripts. Runtime dependencies belong
to the package that consumes them.

```json
{
  "name": "rmax-system",
  "private": true,
  "workspaces": {
    "packages": ["apps/*", "packages/*"],
    "catalog": {"zod": "<pinned-compatible-range>"}
  }
}
```

Do not turn the root package into an implicit dependency container.

### 3. Enable isolated installs

```toml
[install]
linker = "isolated"
```

With isolated linking a package cannot resolve a dependency it never declared,
so phantom-dependency defects surface at install or type-check time instead of
in production. Every package declares every direct dependency it imports.

### 4. Make cross-workspace dependencies explicit

Packages depend on one another through declared workspace dependencies and
exported public APIs. Never use a relative import that escapes the package root
to reach another package's internals.

### 5. Define the public API with `exports`

```json
{
  "name": "@rmax/search",
  "exports": {
    ".": "./src/index.ts",
    "./contracts": "./src/contracts.ts"
  }
}
```

Consumers must not deep-import unexported paths. A package-local `index.ts` may
curate that package's surface; a repository-wide `index.ts` must not become a
hand-maintained registry of every implementation.

### 6. Structure packages around capabilities

```text
src/
  index.ts
  domain/
  application/
  ports/
  adapters/
```

Keep domain and application logic independent of Bun, HTTP, database, and
provider SDKs where practical. Framework-specific code belongs in adapters or
the app composition root. Small packages collapse empty layers.

### 7. Validate at boundaries with Zod, not everywhere

Zod is the default for non-trivial serialized or untrusted TypeScript
boundaries. Plain types and interfaces remain appropriate after validation. Do
not use Zod schemas as containers for authorization, workflow policy, or
stateful business rules; see `zod-boundary-validation` for the mechanics.

### 8. Prefer explicit composition over global registration

Provider and plugin discovery uses explicit constructors, dependency
injection, or generated metadata from per-package manifests. Avoid
import-side-effect registration, one giant provider switch, a hand-edited
repository-level plugin registry, and hidden dependence on module load order.

### 9. Write behavior-oriented, package-local tests

```text
tests/
  contract/
  behavior/
  integration/
```

Use Bun's test runner by default when it satisfies requirements; choose another
framework only for material value, not habit. Tests target package exports and
observable behavior rather than private function structure.

### 10. Expose the canonical verification tasks

```text
fmt       -> bun fmt --check (or the repository-selected formatter)
lint      -> bun lint (or the repository-selected linter)
check     -> bun check / TypeScript verification appropriate to the repo
test      -> bun test
build     -> bun build or application/package build
contract  -> schema/API compatibility checks when applicable
```

Tools stay repository-owned; task names are standardized by ADR-0018 — see
`affected-polyglot-toolchain`.

### 11. Use catalogs for version churn, not to hide dependencies

A shared catalog may centralize versions for foundational packages, but every
consumer still declares the dependency explicitly. Catalog edits are
repository-wide dependency changes and take a broader change class than a
feature edit.

### 12. Avoid configuration mega-files

Prefer package-local configuration extending small root defaults. Root
`tsconfig`, lint, and build settings hold stable policy, not package-specific
behavior. When package conditionals accumulate at the root, move them back to
the owning package.

## Invariants

- One workspace package per capability; `exports` defines its public surface.
- Every imported dependency is declared by the importing package.
- No relative import escapes a package root.
- The root package stays private and runtime-dependency free.
- Contract libraries are separate packages, not copies inside consumers.
- Tests run and pass per package, without the whole workspace.

## Anti-patterns

**Wrong:** `import { search } from "../../search/src/adapters/exa"` across
packages.
**Right:** declare `@rmax/search` as a workspace dependency and import from its
exported entry point.

**Wrong:** relying on a hoisted `zod` that only the root declares.
**Right:** isolated linker plus an explicit dependency in the consuming package.

**Wrong:** adding an entry to a root `registry.ts` for each new provider.
**Right:** a provider package or adapter module, wired at the composition root.

**Wrong:** `tsconfig.json` at the root accumulating per-package paths and
overrides.
**Right:** a minimal root base config, with package-local extension.

## Verification checklist

- [ ] `bun install` succeeds with the isolated linker; no phantom resolution.
- [ ] The changed package declares every dependency it imports.
- [ ] New behavior is reachable through an exported path.
- [ ] No consumer deep-imports an unexported module.
- [ ] Root `package.json` gained no runtime dependency.
- [ ] Boundary inputs are validated with Zod; policy stays in domain code.
- [ ] Package-local `fmt`, `lint`, `check`, `test` pass.
- [ ] No new conditional block was added to a root configuration file.

## Failure and escalation

Escalate when:

- a package cannot be verified without installing the whole workspace;
- a required dependency is only available hoisted and isolation cannot be
  enabled without a migration plan;
- the change needs `bun.lock` or a catalog edit that the task envelope forbids;
- two packages claim the same public export name;
- a package boundary must change to finish the task.

## Handoffs

- `agent-native-modular-architecture` — why the boundaries exist.
- `zod-boundary-validation` — validation and stable domain error codes.
- `affected-polyglot-toolchain` — Moon tasks, affected runs, proto/Buf contracts.
- `machine-readable-capability-graph` — `module.yaml` for the package.
- `agentic-verification-ladder` — required gates.

## Compact example

Adding a provider to `packages/search` adds
`packages/search/src/adapters/<provider>.ts`, exposes it through the existing
`@rmax/search` entry point or a new subpath in `exports`, adds a contract test,
and wires it in `apps/*/src/composition.ts`. No other package changes, no root
dependency is added, and no barrel registry is edited.
