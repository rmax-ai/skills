---
name: zod-boundary-validation
description: >-
  Validate untrusted or serialized data at TypeScript boundaries with Zod v4,
  map issues to stable domain error codes, and keep authorization and workflow
  policy in deterministic domain code. Use when handling request payloads,
  configuration, queue or event envelopes, database rows, or other data
  crossing a trust boundary.
---

# Zod boundary validation

## When this applies

Use a Zod v4 schema when data changes from an untrusted or serialized
representation into typed TypeScript data:

- HTTP request bodies, query-derived payloads, and JSON messages.
- Configuration loaded from files, environment variables, or deployment input.
- Queue and event envelopes received from another process or service.
- Database rows crossing from a persistence adapter into application code.

The boundary adapter owns parsing, normalization, validation, and conversion
to a stable domain result. A trusted internal object that was already produced
by that adapter does not need to be parsed again at every domain call. Fresh
bytes, unknown values, and persistence records are boundary input; typed
objects created under an explicit invariant are trusted according to that
invariant.

Validation is not authorization. A valid request can still be forbidden, stale,
over quota, or invalid for the current workflow. Perform those checks in
deterministic domain or application-policy code after validation.

## Core patterns (Zod v4 APIs)

Use `z.object()` for a record shape and choose the unknown-key policy
explicitly. Use `.parse()` when an exception is the boundary's chosen control
flow and `.safeParse()` when the adapter should return a success or domain
error result:

```ts
import { z } from "zod";

const createAccountSchema = z.strictObject({
  email: z.email(),
  age: z.number().int().nonnegative(),
  requestedAt: z.iso.datetime(),
});

const valid = createAccountSchema.parse({
  email: "a@example.test",
  age: 30,
  requestedAt: "2026-01-01T00:00:00Z",
});

const unknownInput: unknown = {
  email: "a@example.test",
  age: 30,
  requestedAt: "2026-01-01T00:00:00Z",
};
const result = createAccountSchema.safeParse(unknownInput);
if (result.success) {
  const account = result.data;
  const wirePayload = createAccountSchema.parse(account);
}
```

`z.strictObject()` rejects unknown keys. `z.object({...}).strict()` expresses
the same intent on an object schema. `z.object({...}).loose()` intentionally
keeps unknown keys for a documented compatibility boundary. The default
unknown-key behavior of a plain object should not be an accidental contract:
name the policy in the schema and test it.

Defaults and coercion are behavior, not neutral type annotations. A default
can make an omitted field appear present, while `z.coerce.number()` follows
JavaScript number conversion semantics, including surprising edge inputs.
Prefer explicit pre-normalization for formats such as numeric strings,
booleans, empty strings, and timestamps:

```ts
function normalizeInput(raw: Record<string, unknown>) {
  const value = { ...raw };
  if (typeof value.age === "string" && /^[0-9]+$/.test(value.age)) {
    value.age = Number(value.age);
  }
  if (typeof value.enabled === "string") {
    const flag = value.enabled.trim().toLowerCase();
    if (flag === "true" || flag === "false") value.enabled = flag === "true";
  }
  return value;
}

const rawInput: Record<string, unknown> = { age: "30", enabled: "true" };
const compatibilitySchema = z.strictObject({
  age: z.number().int().nonnegative(),
  enabled: z.boolean(),
});
const normalized = compatibilitySchema.safeParse(normalizeInput(rawInput));
```

Use `z.coerce` only when its conversion table is part of the contract and its
edge cases have tests. Normalize documented formats first, then validate the
normalized value. Keep the normalizer at the boundary and do not spread
conversion decisions through domain code.

## Version envelopes and discriminated unions

Put a literal `kind` field in each variant and use
`z.discriminatedUnion("kind", [...])`:

```ts
import { z } from "zod";

const userCreatedV1 = z.strictObject({
  kind: z.literal("user.created"),
  version: z.literal(1),
  userId: z.string(),
});

const userDeletedV1 = z.strictObject({
  kind: z.literal("user.deleted"),
  version: z.literal(1),
  userId: z.string(),
});

const userEventSchema = z.discriminatedUnion("kind", [
  userCreatedV1,
  userDeletedV1,
]);
```

When adding a variant:

1. Add a schema with a unique literal `kind` and explicit `version`.
2. Add it to the discriminated union used by the ingress adapter.
3. Decide which boundaries accept the new variant.
4. Add valid, wrong-kind, wrong-version, missing-field, and unknown-field
   tests.
5. Regenerate or review derived JSON Schema and update downstream contracts.
6. Add domain-policy handling separately; parsing a variant is not permission.

If several versions share a `kind`, use a second literal discriminator or an
explicit migration adapter. Do not silently reinterpret an old payload as a
new shape.

## JSON Schema derivation

Derive a publication or drift artifact from the runtime Zod v4 schema:

```ts
const schemaForClients = z.toJSONSchema(createAccountSchema);
```

`z.toJSONSchema(schema)` is the v4 top-level API. It can publish an input
contract, support generated client checks, or feed a drift test. The runtime
Zod schema is authoritative; JSON Schema is derived output. If a second
consumer contract is unavoidable, test parity for required fields, types,
enums, nullable values, and unknown-key behavior.

## Domain error mapping

Use `safeParse()` at a boundary when a validation failure is an expected
domain result. Inspect `result.error.issues`; each issue has a `code`, `path`,
and `message`. Map the stable issue code and path to an application-owned
domain code. Never make raw issues, messages, or Zod error classes the stable
API contract.

| Zod issue code or location | Domain code |
| --- | --- |
| `invalid_type` at a required field | `input.type` (this example's mapping; use `input.required` only when your adapter distinguishes the missing case) |
| `unrecognized_keys` | `input.unknown_field` |
| `invalid_format` | `input.format` |
| `invalid_union` at the `kind` discriminator (no variant matched) | `input.variant` |
| `invalid_value` at a variant discriminator field (`kind` or `version`) | `input.variant` |
| Any other issue, including `invalid_value` at a non-discriminator field | `input.invalid` |

The adapter can preserve the path for diagnostics while exposing only the
domain code:

```ts
type DomainError = {
  ok: false;
  code: "input.required" | "input.type" | "input.unknown_field" |
    "input.format" | "input.variant" | "input.invalid";
  path: PropertyKey[];
};

type DomainResult<T> = { ok: true; value: T } | DomainError;

const VARIANT_FIELDS: readonly PropertyKey[] = ["kind", "version"];

function mapIssue(issue: { code: string; path: PropertyKey[] }): DomainError {
  const atVariantField =
    issue.path.length === 1 && VARIANT_FIELDS.includes(issue.path[0]);
  const code =
    issue.code === "unrecognized_keys" ? "input.unknown_field" :
    issue.code === "invalid_format" ? "input.format" :
    issue.code === "invalid_union" ? "input.variant" :
    issue.code === "invalid_value" && atVariantField ? "input.variant" :
    issue.code === "invalid_type" ? "input.type" : "input.invalid";
  return { ok: false, code, path: issue.path };
}

function parseAccount(raw: unknown): DomainResult<z.infer<typeof createAccountSchema>> {
  const result = createAccountSchema.safeParse(raw);
  if (!result.success) return mapIssue(result.error.issues[0]);
  return { ok: true, value: result.data };
}
```

For `{ email: "a@example.test", age: "old" }`, the adapter returns a
domain error with `input.type` and the `age` path. For a valid object with an
integer age and timestamp, it returns the parsed data. A transport adapter can
turn those codes into an HTTP response, queue rejection, or log event without
depending on Zod's message wording.

Variant failures have a pinned shape under Zod v4.6.5. An unknown `kind`
fails the union with `invalid_union` reported at the `kind` path, because no
variant matches the discriminator. A known `kind` with an unsupported
`version` selects its variant and then fails the `version` literal with
`invalid_value` at the `version` path. Both mean the payload identifies a
variant this boundary does not support, so both surface as `input.variant`.
Keep the `invalid_value` rule scoped to the variant fields: an ordinary
literal or enum mismatch elsewhere (for example a `state` field) stays
`input.invalid`. `tests/probes/zod-variant-mapping/` pins these cases against
Zod 4.6.5.

## Zod v4 landmines

Verify behavior against the pinned Zod v4 version instead of relying on v3
memory:

- Overriding a key on an object schema containing refinements throws
  `Cannot overwrite keys on object schemas containing refinements — use .safeExtend()`.
  Use `.safeExtend()` when the replacement schema is assignable and the
  refinement must be preserved.
- `.safeExtend()` exists and works for refined bases. Adding a **new** key with
  plain `.extend()` on a refined base does not throw; the trigger is
  overwriting an existing key. Test both cases so a workaround does not hide
  the actual failure mode.
- `.refine()` runs after the fields have been defined and parsed. Extension
  ordering follows the field definitions: establish the durable field shape
  first, then add refinements whose inputs are present in that shape.
- Chaining extensions of already-extended schemas is a smell. Keep a shared
  field-shape object, then spread it into a durable base and extend that base
  for each intentional variant.
- Use top-level formats such as `z.email()` where the v4 API provides them.
  Do not assume a v3-era method or helper remains the right spelling without
  checking the pinned version.

An executable probe for the refinement rules should assert the throw on key
overwrite, success for `.safeExtend()`, and success for adding a new key with
`.extend()`. Keep that probe in verification tooling (`tests/probes/`) rather
than in a production boundary adapter.

## Anti-patterns

### Re-parsing every internal object

**Wrong:** Call `createAccountSchema.parse(account)` in every domain function
after `account` already came from the ingress adapter.

**Right:** Parse once at ingress, pass the inferred value through trusted
domain code, and parse again only at a new trust boundary.

### Authorization or stateful policy in refinements

**Wrong:** Put a database lookup, current-user permission check, clock check,
or quota decision inside `.refine()`.

**Right:** Validate shape and types first, then call deterministic application
policy with the parsed value and an explicit policy context.

### Raw Zod issues as a machine contract

**Wrong:** Return `result.error.issues` or `issue.message` directly and make
clients branch on wording from the validation library.

**Right:** Map `code` and `path` to stable domain codes and keep raw issues in
internal diagnostics only.

### Duplicate schemas without parity tests

**Wrong:** Maintain a separate JSON Schema and Zod schema with no parity test
for required fields, enums, formats, and unknown-key behavior.

**Right:** Derive JSON Schema with `z.toJSONSchema()` or test every deliberate
parity boundary when a second contract is unavoidable.

### Type casts that bypass validation

**Wrong:** Use `raw as z.infer<typeof createAccountSchema>` for an unknown
payload, or discard a failed `safeParse()` result and continue.

**Right:** Keep the value `unknown`, use `.parse()` or `.safeParse()` at the
boundary, and handle every failure with a domain result.

## Verification guidance

Boundary tests should assert domain behavior rather than library prose:

- Pass malformed JSON, a non-object root, missing fields, and wrong literal
  discriminators.
- Pass unknown fields through a `z.strictObject()` schema and assert
  `input.unknown_field`.
- Test numeric strings, booleans, empty strings, timestamp formats, defaults,
  and `z.coerce.number()` edge cases explicitly.
- Assert `input.required`, `input.type`, `input.unknown_field`,
  `input.format`, `input.variant`, or `input.invalid`, never a Zod message.
- Assert `input.variant` for an unknown `kind` and for a wrong `version` on a
  matched `kind`, and `input.invalid` for an ordinary non-discriminator
  literal mismatch, so the variant rule cannot over-map.
- Add a strict-mode gotcha test proving that an otherwise coercible value is
  rejected until the adapter normalizes it.
- If a separate schema is published, compare required fields, types, enum
  values, formats, and additional-property behavior in a parity test.
- Run a pinned v4 probe for refinement overwrite, `.safeExtend()`, new-key
  `.extend()`, top-level `z.email()`, and `z.toJSONSchema()`.
- Run the pinned Zod 4.6.5 variant-mapping probe in
  `tests/probes/zod-variant-mapping/` when changing the envelope or mapping
  rules.
