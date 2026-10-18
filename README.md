# Portable agent skills

This repository contains small, runtime-neutral skills for boundary validation
and bounded agent-workflow protocols.
The source is public and is intended to be installed into Hermes, Codex, or
Droid through reviewed pull requests.

## Layout

| Path | Purpose |
| --- | --- |
| `portable/` | Portable skill source directories. |
| `catalog/skills.json` | Machine-readable skill metadata and integrity hashes. |
| `profiles/` | Example copy-install profiles for supported runtimes. |
| `scripts/catalog_check.py` | Deterministic catalog and source validation. |
| `scripts/materialize.py` | Dry-run, check, and guarded copy installer. |
| `tests/` | Offline unit tests and small synthetic fixtures. |
| `tests/probes/` | Manual pinned-toolchain probes (not part of dependency-free CI). |
| `.github/workflows/ci.yml` | Public, dependency-free CI checks. |

## Agentic development suite (ADR-0014..0022)

The catalog carries one skill per accepted architecture decision for
agent-developed software. The mapping is 1:1 and is enforced by
`tests/test_adr_skill_suite.py`: one ADR, one skill, no reused decision number.

| ADR | Portable skill |
| --- | --- |
| ADR-0014 | `portable/agent-native-modular-architecture` |
| ADR-0015 | `portable/python-capability-workspace` |
| ADR-0016 | `portable/typescript-bun-capability-workspace` |
| ADR-0017 | `portable/rust-capability-workspace` |
| ADR-0018 | `portable/affected-polyglot-toolchain` |
| ADR-0019 | `portable/machine-readable-capability-graph` |
| ADR-0020 | `portable/change-envelope-planning` |
| ADR-0021 | `portable/agentic-verification-ladder` |
| ADR-0022 | `portable/token-efficient-repository-context` |

The suite is layered rather than nine independent essays:

```text
architecture shape        ADR-0014
  language layout         ADR-0015 / 0016 / 0017
  tool + affected graph   ADR-0018
  ownership graph         ADR-0019
  change envelopes        ADR-0020
  verification gates      ADR-0021
  context economics       ADR-0022
```

These skills are runtime-neutral guidance only. They declare no dependencies,
make no network calls, and reach runtimes through the same catalog and profile
copy-install mechanism as every other entry, so no second distribution path
exists.

## Validation

Run the complete offline test suite:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/catalog_check.py check
python3 scripts/materialize.py --check --profile profiles/<x>.json --source .
```

The materializer is a dry run unless `--apply` is supplied. Profiles may use
runtime-specific home placeholders, so configure those placeholders before a
check or install.

Pinned probes are manual, require a network install of the pinned toolchain,
and are not part of CI:

```sh
cd tests/probes/zod-variant-mapping
npm install --ignore-scripts --no-audit --no-fund
node variant-mapping.mjs
```

## Review policy

Changes land through pull requests only. Reviewers check that content is
public-safe, deterministic, portable, and limited to the documented skill
scope. The catalog hash must be refreshed whenever a skill file changes.

## Scope limits

The repository provides guidance and local tooling only. It does not contain
runtime-specific orchestration, network clients, credentials, deployment
configuration, or application business policy.
