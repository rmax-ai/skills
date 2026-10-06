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
