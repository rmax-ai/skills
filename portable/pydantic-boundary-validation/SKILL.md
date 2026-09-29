---
name: pydantic-boundary-validation
description: >-
  Validate untrusted or serialized data at Python boundaries with Pydantic v2,
  map validation failures to stable domain error codes, and keep authorization
  and workflow policy out of validators. Use when handling request payloads,
  configuration, queue or event envelopes, database rows, or other data
  crossing a trust boundary.
---

# Pydantic boundary validation

## When this applies

Use a Pydantic v2 model at the point where data changes from an untrusted or
serialized representation into typed application data:

- HTTP request bodies, query-derived payloads, and JSON messages.
- Configuration files loaded from disk or environment-backed sources.
- Queue and event envelopes received from another process or service.
- Database rows crossing from a persistence adapter into typed application
  code.

The boundary adapter owns parsing, normalization, validation, and conversion
to a stable domain result. A trusted internal object that was already produced
by that adapter does not need to be re-validated every time it moves between
domain functions. Keep the trust decision explicit: data returned from a
domain constructor is trusted according to that constructor's invariant, while
fresh bytes, mappings, and persistence records are boundary input.

Validation is not authorization. A valid request can still be forbidden, stale,
over quota, or invalid for the current workflow. Perform those checks in
deterministic domain or application-policy code after validation.

## Core patterns (Pydantic v2 APIs)

Use `BaseModel` for named records and `TypeAdapter` for a non-model type such
as a list, scalar, mapping, or union. Use the v2 entry points at the boundary
and at egress:

```python
from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class CreateAccount(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    email: str
    age: int
    requested_at: datetime


class AccountCreated(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    kind: Literal["account.created"]
    account_id: str


class AccountClosed(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    kind: Literal["account.closed"]
    account_id: str


Event = Annotated[
    Union[AccountCreated, AccountClosed],
    Field(discriminator="kind"),
]
EventAdapter = TypeAdapter(Event)

account = CreateAccount.model_validate({"email": "a@example.test", "age": 30,
                                        "requested_at": datetime.now()})
event = EventAdapter.validate_python(
    {"kind": "account.created", "account_id": "acct-1"}
)

wire_payload = account.model_dump(mode="json")
wire_json = account.model_dump_json()
```

Use `model_validate` for a Python mapping or object and
`model_validate_json` for a JSON string or bytes payload. Use
`TypeAdapter.validate_python` or `TypeAdapter.validate_json` when the type is
not naturally a model. At egress, `model_dump` is useful for a controlled
mapping and `model_dump_json` is useful for a JSON wire representation. Do not
call a v1 method merely because its name is familiar.

### Strictness and extra keys

Set the policy deliberately with `ConfigDict`:

```python
class StrictCommand(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    command: str


class CompatibilityRecord(BaseModel):
    model_config = ConfigDict(strict=False, extra="ignore")
    display_name: str
```

`strict=True` is a good default for a typed command or a security-sensitive
boundary when the producer can send the intended JSON types. It rejects
surprising conversions and makes producer drift visible. `extra="forbid"`
rejects unknown keys and is useful when the contract is closed. An explicitly
lenient adapter can use `strict=False` and `extra="ignore"` for a versioned
compatibility boundary where ignoring unrelated producer fields is part of the
documented contract. Never choose leniency just to make a failing payload pass.

Strictness does not make ambiguous serialized formats safe by itself. For
example, integer-to-string conversion, boolean-versus-integer confusion, and
datetime parsing can hide producer bugs. Normalize edge formats explicitly
before validation, then validate the normalized value:

```python
def normalize_command(raw: dict[str, object]) -> dict[str, object]:
    value = dict(raw)
    age = value.get("age")
    if isinstance(age, str) and age.isdecimal():
        value["age"] = int(age)
    if isinstance(value.get("enabled"), str):
        normalized = value["enabled"].strip().lower()
        if normalized in {"true", "false"}:
            value["enabled"] = normalized == "true"
    # Parse a documented datetime format in this adapter instead of relying
    # on an incidental coercion rule.
    return value
```

Keep normalization small and format-specific. Record whether a conversion was
allowed by the input contract, and test booleans, numeric strings, empty
strings, timezone offsets, and already-typed values separately.

## Version envelopes and discriminated unions

Put a literal discriminator in every versioned or variant envelope. The
discriminator should select a closed set of payload models, not execute
workflow policy:

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, ConfigDict, Field


class UserCreatedV1(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    kind: Literal["user.created"]
    version: Literal[1]
    user_id: str


class UserDeletedV1(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    kind: Literal["user.deleted"]
    version: Literal[1]
    user_id: str


UserEvent = Annotated[
    Union[UserCreatedV1, UserDeletedV1],
    Field(discriminator="kind"),
]
```

When adding a variant:

1. Add a model with a unique literal `kind` and an explicit `version`.
2. Add it to the `Union` used by the discriminated adapter.
3. Decide whether the new variant is allowed at each ingress boundary.
4. Add valid, wrong-kind, missing-field, and unknown-field tests.
5. Regenerate or review derived JSON Schema and update downstream contracts.
6. Add domain-policy handling separately; a parsed variant is not permission.

If versions share a `kind`, use a second literal discriminator or a deliberate
version migration adapter. Do not silently reinterpret an old payload as a
new model.

## JSON Schema derivation

Derive publication and drift artifacts from the runtime model:

```python
schema = CreateAccount.model_json_schema()
```

`model_json_schema()` can publish an input contract, drive generated client
checks, or support a drift test against a checked-in contract. The runtime
Pydantic model is authoritative; JSON Schema is derived output. If a separate
consumer schema must exist, test parity for required fields, types, enums,
unknown-key behavior, and nullable values rather than maintaining two
independent sources of truth.

## Domain error mapping

`ValidationError` is an adapter concern. Catch it at the boundary, inspect
`.errors()`, and map each error's stable `type` and `loc` to an application
code. Do not expose Pydantic classes, raw messages, or the complete error
structure as an API contract.

| Pydantic error type or location | Domain code |
| --- | --- |
| `missing` | `input.required` |
| `extra_forbidden` | `input.unknown_field` |
| `int_type`, `string_type`, `bool_type`, `datetime_type` | `input.type` |
| `union_tag_invalid`, `union_tag_not_found` | `input.variant` |
| Any other validation failure | `input.invalid` |

The mapping is owned by the application and can remain stable when Pydantic
changes its wording or exception class:

```python
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError


@dataclass(frozen=True)
class DomainError:
    code: str
    location: tuple[str | int, ...]


def _map_validation_error(exc: ValidationError) -> DomainError:
    first = exc.errors()[0]
    error_type = str(first.get("type", ""))
    if error_type == "missing":
        code = "input.required"
    elif error_type == "extra_forbidden":
        code = "input.unknown_field"
    elif error_type in {
        "int_type", "string_type", "bool_type", "datetime_type",
    }:
        code = "input.type"
    elif error_type in {"union_tag_invalid", "union_tag_not_found"}:
        code = "input.variant"
    else:
        code = "input.invalid"
    return DomainError(code=code, location=tuple(first.get("loc", ())))


def parse_account(raw: Mapping[str, Any] | str | bytes) -> CreateAccount | DomainError:
    try:
        if isinstance(raw, (str, bytes)):
            return CreateAccount.model_validate_json(raw)
        return CreateAccount.model_validate(raw)
    except ValidationError as exc:
        return _map_validation_error(exc)
```

For `{"email": "a@example.test", "age": "old"}`, the adapter returns
`DomainError(code="input.type", location=("age",))`. For a valid mapping with
an integer age, it returns a `CreateAccount` instance. The caller can turn
those domain codes into an HTTP response, queue rejection, or log event
without depending on Pydantic's message text.

## Anti-patterns

### Re-validating every internal object

**Wrong:** Call `CreateAccount.model_validate(account.model_dump())` in every
domain function, even though `account` came from the one ingress adapter.

**Right:** Validate once at ingress, pass the typed object through trusted
domain code, and validate again only when it crosses a new trust boundary.

### Authorization or stateful policy in validators

**Wrong:** Add a validator that reads the current user's permissions, database
state, clock, or quota to decide whether a field is allowed.

**Right:** Validate shape and types first, then call deterministic application
policy with the validated object and an explicit policy context.

### Raw library errors as a machine contract

**Wrong:** Return `str(exc)` or `exc.errors()` directly to clients and make
callers branch on Pydantic message text.

**Right:** Map `.errors()` `type` and `loc` to stable domain codes and keep
library details in internal diagnostics.

### Duplicate schemas without parity tests

**Wrong:** Maintain a hand-written JSON Schema and a Pydantic model with no
parity check between required fields, enums, and extra-key behavior.

**Right:** Derive JSON Schema with `model_json_schema()` or add an explicit
parity test whenever a second contract is unavoidable.

### Pydantic v1 leftovers in v2 code

**Wrong:** Use `parse_obj`, `.dict()`, `.schema()`, `__fields__`, or
`root_validator` in a new v2 boundary adapter.

**Right:** Use `model_validate`, `model_dump`, `model_json_schema()`, current
model metadata, and v2 field or model validators only when a validation rule
is genuinely structural.

## Verification guidance

Boundary tests should exercise behavior, not library prose:

- Pass malformed JSON, a non-object root, missing fields, and wrong literal
  discriminators.
- Pass unknown fields and assert the `extra="forbid"` domain code.
- Test numeric strings, booleans, datetime strings, empty strings, and timezone
  variants so every deliberate normalization rule is visible.
- Assert `input.required`, `input.unknown_field`, `input.type`,
  `input.variant`, or `input.invalid`, never a Pydantic message.
- Add a strict-mode gotcha test proving that a value which would otherwise be
  coerced is rejected until the adapter normalizes it.
- If a separate schema is published, compare required fields, types, enum
  values, and additional-property behavior in a parity test.
- Test egress with both `model_dump(mode="json")` and `model_dump_json()` so
  datetime and other JSON encodings are intentional.
