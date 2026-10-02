# Zod variant-mapping probe (pinned)

Manual verification for the "Domain error mapping" contract in
`portable/zod-boundary-validation/SKILL.md`, pinned to **zod 4.6.5**.

The probe builds the skill's envelope example and asserts, for each case, the
raw Zod issue `code`/`path` and the domain code produced by the documented
`mapIssue()`:

1. valid envelope (control) — parses without issues.
2. unknown `kind` — `invalid_union` @ `["kind"]` → `input.variant`.
3. known `kind` + wrong `version` — `invalid_value` @ `["version"]` → `input.variant`.
4. ordinary non-discriminator literal mismatch — `invalid_value` @ `["state"]` → `input.invalid`.
5. ordinary non-discriminator union failure — `invalid_union` @ `["retry"]` → `input.invalid`.

Run (requires Node and network access for the pinned install; not part of the
dependency-free CI):

```sh
cd tests/probes/zod-variant-mapping
npm install --ignore-scripts --no-audit --no-fund
node variant-mapping.mjs
```

Exit codes: `0` = all cases reproduced on the pinned version; `1` = version
drift or a missing dependency. `node_modules/` and `package-lock.json` are
local install output and must not be committed.
