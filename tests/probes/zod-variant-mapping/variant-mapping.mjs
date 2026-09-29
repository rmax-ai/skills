#!/usr/bin/env node
// Pinned probe — Zod variant-identity error mapping (pinned toolchain: zod 4.6.5).
//
// Verifies the "Domain error mapping" contract in
// portable/zod-boundary-validation/SKILL.md against the pinned Zod release:
//
//   1. unknown `kind`                       -> invalid_union @ ["kind"]   -> input.variant
//   2. known `kind` + unsupported `version` -> invalid_value @ ["version"] -> input.variant
//   3. non-discriminator literal mismatch   -> invalid_value @ ["state"]   -> input.invalid
//   4. valid envelope control               -> parses without issues
//
// Manual run (not part of the dependency-free CI):
//
//   cd tests/probes/zod-variant-mapping
//   npm install --ignore-scripts --no-audit --no-fund
//   node variant-mapping.mjs
//
// Exit code 0 = every pinned case reproduced; exit code 1 = drift or missing dependency.

import { readFileSync } from "node:fs";

const PINNED_ZOD = "4.6.5";

let z;
try {
  ({ z } = await import("zod"));
} catch (error) {
  console.error(
    `zod is not resolvable (${error?.code ?? error?.message ?? error}); ` +
      "run \"npm install --ignore-scripts --no-audit --no-fund\" in this directory first",
  );
  process.exit(1);
}

let installedVersion;
try {
  installedVersion = JSON.parse(
    readFileSync(new URL("./node_modules/zod/package.json", import.meta.url), "utf8"),
  ).version;
} catch {
  installedVersion = undefined;
}
if (installedVersion !== PINNED_ZOD) {
  console.error(
    `drift: this probe pins zod ${PINNED_ZOD}, found ${installedVersion ?? "none"} ` +
      "(install the pinned version in this directory)",
  );
  process.exit(1);
}

// Envelope schema from the skill: a literal `kind` plus an explicit literal
// `version` per variant, combined with z.discriminatedUnion("kind", [...]).
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
const userEventSchema = z.discriminatedUnion("kind", [userCreatedV1, userDeletedV1]);

// A schema with an ordinary (non-discriminator) literal that must NOT map to
// the variant code.
const accountSchema = z.strictObject({
  email: z.email(),
  state: z.literal("active"),
});

// The documented adapter mapping — mirror of mapIssue() in the skill.
const VARIANT_FIELDS = ["kind", "version"];
function mapIssue(issue) {
  const atVariantField =
    issue.path.length === 1 && VARIANT_FIELDS.includes(issue.path[0]);
  const code =
    issue.code === "unrecognized_keys" ? "input.unknown_field" :
    issue.code === "invalid_format" ? "input.format" :
    issue.code === "invalid_union" ? "input.variant" :
    issue.code === "invalid_value" && atVariantField ? "input.variant" :
    issue.code === "invalid_type" ? "input.type" : "input.invalid";
  return { code, path: issue.path };
}

function firstIssue(schema, input) {
  const result = schema.safeParse(input);
  return result.success ? undefined : result.error.issues[0];
}

const cases = [
  {
    name: "valid envelope (control)",
    schema: userEventSchema,
    input: { kind: "user.created", version: 1, userId: "u1" },
    expectSuccess: true,
  },
  {
    name: "unknown kind",
    schema: userEventSchema,
    input: { kind: "user.renamed", version: 1, userId: "u1" },
    issue: { code: "invalid_union", path: ["kind"] },
    domain: "input.variant",
  },
  {
    name: "known kind + wrong version",
    schema: userEventSchema,
    input: { kind: "user.created", version: 2, userId: "u1" },
    issue: { code: "invalid_value", path: ["version"] },
    domain: "input.variant",
  },
  {
    name: "non-discriminator literal mismatch",
    schema: accountSchema,
    input: { email: "a@example.test", state: "paused" },
    issue: { code: "invalid_value", path: ["state"] },
    domain: "input.invalid",
  },
];

let failures = 0;
for (const testCase of cases) {
  const issue = firstIssue(testCase.schema, testCase.input);
  if (testCase.expectSuccess) {
    const ok = issue === undefined;
    if (!ok) failures += 1;
    console.log(`${ok ? "PASS" : "FAIL"} ${testCase.name}: parsed without issues`);
    continue;
  }
  if (issue === undefined) {
    failures += 1;
    console.log(`FAIL ${testCase.name}: unexpectedly parsed`);
    continue;
  }
  const rawOk =
    issue.code === testCase.issue.code &&
    JSON.stringify(issue.path) === JSON.stringify(testCase.issue.path);
  const mapped = mapIssue(issue);
  const domainOk = mapped.code === testCase.domain;
  const ok = rawOk && domainOk;
  if (!ok) failures += 1;
  console.log(
    `${ok ? "PASS" : "FAIL"} ${testCase.name}: issue=${issue.code} ` +
      `path=${JSON.stringify(issue.path)} -> ${mapped.code} ` +
      `(expected issue=${testCase.issue.code} path=${JSON.stringify(testCase.issue.path)} ` +
      `-> ${testCase.domain})`,
  );
}

if (failures > 0) {
  console.error(`probe FAILED: ${failures} case(s) drifted on zod ${installedVersion}`);
  process.exit(1);
}
console.log(`probe OK: ${cases.length} cases pinned on zod ${installedVersion}`);
