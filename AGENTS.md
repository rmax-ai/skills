# Repository agent policy

## Allowed work

Agents may add or improve portable skill content, catalog metadata, profiles,
stdlib-only validation tooling, tests, fixtures, and the CI workflow. Work
must remain within the repository tree and must preserve deterministic output.

## Hard boundaries

- Keep all content public-safe. Do not add private paths, personal identifiers,
  credential-shaped values, or employer or client references.
- Do not add dependencies, network calls, generated artifacts, or unrelated
  skills.
- Commits and merges are operator-owned. Agents must not commit, push, merge,
  rewrite history, or edit `main` directly.
- Use pull requests for review and keep changes limited to the requested scope.

## Validation battery

Before handing off a change, run:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/catalog_check.py check
python3 -m compileall -q scripts tests
git diff --check
git status --short
HERMES_HOME="$(mktemp -d)"
export HERMES_HOME
profile=tests/fixtures/materialize-ci-profile.json
python3 scripts/materialize.py --profile "$profile" --source .
python3 scripts/materialize.py --profile "$profile" --source . --apply
python3 scripts/materialize.py --profile "$profile" --source . --check
```

`catalog_check.py check` verifies stored source hashes for every catalog entry.
Use `catalog_check.py --hash DIR` to compute a replacement digest when updating
catalog metadata; it is not an additional validation check.

Also inspect line counts and confirm that unfinished-work markers are absent.

## Style

Use concise Markdown, explicit boundary examples, stable terminology, and
stdlib-only Python tooling. Prefer sorted traversal, canonical JSON, explicit
error handling, and tests that assert domain behavior instead of library
wording.
