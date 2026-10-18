---
name: token-efficient-repository-context
description: >-
  Build agent context architectural-first: envelope, module metadata, contracts,
  then the smallest implementation slice, with progressive disclosure and
  question-driven expansion. Use when starting a task in an unfamiliar
  repository, when context fills with irrelevant code, or when handing work to
  another agent.
---

# Token-efficient repository context

## Source

ADR-0022, *Token-efficient agent context and repository navigation contract*,
merged in `rmax-ai/architecture#15` (merge commit `6fbba39`). Related: ADR-0005,
ADR-0014, ADR-0019, ADR-0020, ADR-0021.

## Purpose

Make the *relevant* context cheap to find: ownership, dependencies, contracts,
public entry points, acceptance criteria, changed files, and verification tasks
before any source-level exploration. Token efficiency is a repository
architecture property, not only a retrieval or model property.

The target is **minimum context required for a safely integrated change** — not
the smallest possible token count.

## When to use

Use this skill when:

- beginning a task in a repository you have not fully loaded;
- a session is spending its budget reading unrelated implementation;
- choosing between exact lookup, scoped search, and broad retrieval;
- preparing review context for someone else;
- writing a handoff to another agent or to the operator;
- deciding whether a module needs a context capsule.

## Required inputs

Collect, or state as unknown:

- `task`: the intent and the change envelope, if one exists;
- `metadata`: whether module manifests, the project graph, and language
  manifests are available;
- `changed_files`: the current diff, if any;
- `contracts`: the public surfaces the task touches;
- `verification`: the tasks the gates will run;
- `unknowns`: the specific questions current context cannot answer.

## Procedure

### 1. Construct context from architecture outward

```text
1. task intent + ChangeEnvelope
2. owning capability/module metadata
3. public contracts and entry points
4. dependency/consumer graph relevant to the change
5. closest behavior/contract tests
6. implementation files required to make the change
7. additional evidence only when a concrete question requires it
```

Do not begin by ingesting the repository. Loading order is the whole method.

### 2. Use machine-readable scope before semantic search

Where capability metadata and the project graph are available, determine the
owning module, allowed mutation paths, public API, direct dependencies and
dependents, relevant verification tasks, and contract edges *before* broad code
retrieval.

Structural metadata is cheaper and more deterministic than asking a model to
infer architecture from source.

### 3. Follow progressive disclosure when navigating

```text
exact symbol/path/error known
  -> grep/symbol/path lookup

module known, behavior unclear
  -> local semantic/code search within the module and direct interfaces

module unknown
  -> architecture graph / project metadata -> bounded search

cross-cutting behavior genuinely unknown
  -> broaden search across declared dependents/contracts
```

Semantic retrieval tools may be used where they measurably improve
localization; they must not replace exact search when the identifier is already
known.

### 4. Make contracts readable without implementation traversal

A non-trivial capability should let an agent answer, from compact metadata or
documentation:

```text
What does this module own?
What does it expose?
What does it consume?
What invariants matter?
How is it verified?
What must not be changed casually?
```

Sources: the module manifest, package exports, protocol definitions, API docs,
and a short module README. Do not write long narrative architecture documents
that duplicate the codebase.

### 5. Keep context capsules compact

A module README or equivalent capsule contains only durable information:
purpose and responsibility, public entry points, important contracts and
invariants, dependency direction, canonical local verification commands, and
links to deeper design documents.

Keep out: changelogs, transient implementation notes, copied source excerpts,
and tutorials.

### 6. Exclude generated and low-information files by default

```text
lockfiles
generated protocol/client code
vendored dependencies
build output
snapshots unrelated to the task
large fixture corpora
coverage artifacts
minified/bundled output
```

Read them only when the task concerns dependency resolution, generation drift,
fixtures, or build output.

### 7. Deduplicate context by authority

```text
contract schema > copied documentation excerpt
package manifest > README dependency list
Moon task definition > prose command list
current source > stale implementation note
accepted ADR > repeated prompt convention
```

Do not carry multiple restatements of the same rule; carry the authoritative one
and a pointer.

### 8. Expand by question, not by "read the relevant files"

```text
Which adapter maps provider errors to SearchError?
Which consumers depend on search.v1?
Where is retry policy applied?
Which test demonstrates cancellation semantics?
```

Each expansion is traceable to an uncertainty. Broad expansion without a
question is how context budgets disappear.

### 9. Keep review context patch-centric

A reviewer receives intent and envelope, changed-file summary or diff, changed
public contracts, relevant invariants, verification evidence, and the small
amount of surrounding source needed to judge behavior. The full implementation
context the coding agent used is not reloaded unless review uncovers a specific
need.

### 10. Hand off summaries plus durable references

A handoff contains result or verdict, decisions made, unresolved risk or
blocker, exact revision/PR/issue references, affected modules and contracts, and
a verification summary. Raw reasoning transcripts and full tool logs are not the
handoff format.

### 11. Measure context efficiency

Where telemetry permits, track input/context tokens per successful task, files
read before the first correct edit, unique files inspected, context tokens
before first edit, repeated reads and searches, retrieval calls, and
post-retrieval fallback burden. Use them to improve metadata, retrieval policy,
skills, and layout.

Never trade correctness for token count.

### 12. Let retrieval benchmarks change tools, not architecture

Code-retrieval benchmark results may change which retrieval tool is preferred
for a task class. They do not remove the need for explicit ownership, contracts,
and dependency metadata. Retrieval operates within or on top of architectural
boundaries rather than compensating indefinitely for missing architecture.

## Invariants

- Context is built in architecture order, not file order.
- Metadata precedes search; search precedes broad reading.
- Every context expansion answers a stated question.
- Authoritative sources replace restatements.
- Generated and low-information files are opt-in.
- Review and handoff carry evidence plus references, not transcripts.
- Correctness outranks token economy.

## Anti-patterns

**Wrong:** starting with a recursive read of the repository, then planning.
**Right:** envelope, module metadata, contracts, then the two files that must
change.

**Wrong:** loading a lockfile or generated bindings to understand a behavior bug.
**Right:** load them only for dependency or generation questions.

**Wrong:** three files all restating the dependency direction, all in context.
**Right:** the manifest that owns the fact, plus a pointer.

**Wrong:** "read all files under the search package" because the module is known.
**Right:** grep the exact symbol, then read the smallest enclosing behavior.

**Wrong:** a handoff that is a transcript dump.
**Right:** verdict, decisions, blocker, revisions, modules, gates.

## Verification checklist

- [ ] A written context order was followed and is recoverable.
- [ ] Ownership and contracts were established before code reading.
- [ ] Each additional file read maps to a question or an envelope path.
- [ ] No lockfile, generated artifact, or vendored tree was loaded without cause.
- [ ] The authority for each duplicated fact is identified once.
- [ ] Review context contains diff, contracts, invariants, and evidence.
- [ ] The handoff names exact revisions, modules, and gate results.
- [ ] Total context stayed proportionate to a single-module change.

## Failure and escalation

Escalate when:

- ownership cannot be determined from metadata (fix the graph, do not guess);
- the task genuinely spans multiple modules without an envelope;
- needed behavior is visible only in generated or vendored code;
- metadata contradicts source and neither is obviously authoritative;
- a reviewer asks for full implementation context because the patch is not
  self-explanatory — treat that as a design or evidence gap.

## Handoffs

- `machine-readable-capability-graph` — the metadata that makes scoping cheap.
- `change-envelope-planning` — supplies intent, class, and allowed paths.
- `agentic-verification-ladder` — supplies the evidence a reviewer needs.
- `agent-native-modular-architecture` — the structure that makes context
  boundaries real.

## Compact example

Task: "provider timeout is not mapped to a search error". Context order:
envelope (L1, search package paths); module manifest → entry point and provider
port; the search contract; the contract test asserting error mapping; then the
provider adapter and the error-mapping table. Five files, one question, no
repository sweep. The PR carries the evidence record and the diff; the reviewer
does not receive the agent's transcript.
