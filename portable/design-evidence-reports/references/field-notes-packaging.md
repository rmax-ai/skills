# Field notes: case-derived packaging decision (issue-357)

## Existing owner check, live inventory

Searched the local skill inventory and the portable catalog before adding a new
entry. Nearest neighbours and the reason none of them owns this responsibility:

| Candidate | What it owns | Why it is not this skill |
| --- | --- | --- |
| `technical-writing-evaluator` | prose quality, evidence-based evaluation | judges text, not figures, page composition or rendered output |
| `mermaid-diagrams` | diagram source and render commands | implementation only; no evidence contract, no reader-question choice |
| `publish-*` / publishing | build, deploy, link handoff | mechanical delivery; a green deploy is not a visual review |
| `claim-driven-software-verification` | whether a claim is supported | does not cover visual form or page composition |
| `eval-rubric-authoring` / `benchmark-scorecard` | scoring criteria and scorecards | defines criteria; does not design a report artifact |
| `slack-queue-state-reactions` | a chat-protocol surface | unrelated surface |

Decision: the responsibility (relationship between evidence, visual form, page
composition and rendered reader experience) has no owner. Add one controller
and compose with the owners above. Do not absorb their duties.

## Catalog provenance note

`catalog/skills.json` requires both `provenance.adr` and `provenance.issue` for
every entry. This skill is case-derived and has no architecture decision record.
The `adr` field states that explicitly (`case-derived: no architecture decision
record; origin <public report reference>`) rather than inventing an accepted ADR
number. Any future tightening of the catalog schema to allow a null `adr` should
be a separate catalog change, not a silent claim in this entry.

## Loader route as found on rmax-10 (2026-11-22)

- `~/.hermes/config.yaml` → `skills.external_dirs: [<operator-kit>/skills]`.
- `rmax-ai/skills` is the portable source of truth; `operator-kit` holds copies
  refreshed by `scripts/materialize.py --profile profiles/rmax-10.json --source .`.
- `materialize.py --check` currently reports drift for
  `engineering/pydantic-boundary-validation/SKILL.md` in operator-kit: the copy
  carries a revision not present in the portable source. That drift predates
  this change. A blanket `--apply` would overwrite the operator-kit copy with
  the older portable revision, so refresh must stay scoped to the new skill id
  until the pydantic drift is reconciled by its owner.
- Observed while validating this skill: a temporary copy placed directly under
`~<hermes-home>/skills/engineering/<id>` *is* reachable by a fresh session (that
is how the behavioral cases ran), but it is a second runtime copy — it defeats
the single-exposure intent and will shadow or be shadowed by the operator-kit
copy once the refresh lands. Remove it after the refresh.

A new catalog entry therefore does **not** reach the Hermes loader on its own.
  Publication is two steps: merge the portable revision, then refresh the copy
  in operator-kit. Both are operator-owned.
