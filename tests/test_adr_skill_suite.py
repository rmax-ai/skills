from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads(
    (ROOT / "catalog" / "skills.json").read_text(encoding="utf-8")
)
ISSUE_REF = "rmax-ai/delegation-queue#214"
MERGE_REF = "rmax-ai/architecture#15"
MERGE_COMMIT = "6fbba39"

# The durable 1:1 mapping between an architecture decision and the one skill
# that carries its operating guidance. Order is the suite order in the ADR set.
ADR_SKILLS = {
    "ADR-0014": "agent-native-modular-architecture",
    "ADR-0015": "python-capability-workspace",
    "ADR-0016": "typescript-bun-capability-workspace",
    "ADR-0017": "rust-capability-workspace",
    "ADR-0018": "affected-polyglot-toolchain",
    "ADR-0019": "machine-readable-capability-graph",
    "ADR-0020": "change-envelope-planning",
    "ADR-0021": "agentic-verification-ladder",
    "ADR-0022": "token-efficient-repository-context",
}

REQUIRED_SECTIONS = (
    "## Source",
    "## Purpose",
    "## When to use",
    "## Invariants",
    "## Anti-patterns",
    "## Verification checklist",
    "## Failure and escalation",
    "## Handoffs",
)

# Each ADR owns a small set of load-bearing terms. If a suite term disappears
# the skill has drifted from the decision it exists to carry.
OWNED_TOKENS = {
    "agent-native-modular-architecture": (
        "capability module",
        "expand-and-contract",
        "hot file",
        "extension over central mutation",
    ),
    "python-capability-workspace": (
        "tool.uv.workspace",
        "src/",
        "ports/",
        "adapters/",
        "uv.lock",
    ),
    "typescript-bun-capability-workspace": (
        'linker = "isolated"',
        "exports",
        "phantom",
        "workspaces",
    ),
    "rust-capability-workspace": (
        "pub(crate)",
        "workspace.dependencies",
        "Cargo.lock",
        "Compose at application roots",
    ),
    "affected-polyglot-toolchain": (
        "moon query affected",
        "buf breaking",
        "protobuf",
        "mise",
    ),
    "machine-readable-capability-graph": (
        "module.yaml",
        "public_entrypoints",
        "central registry",
    ),
    "change-envelope-planning": (
        "allowed_paths",
        "forbidden_paths",
        "L0",
        "L3",
    ),
    "agentic-verification-ladder": (
        "V0",
        "V3",
        "V5",
        "schema_version: 1",
    ),
    "token-efficient-repository-context": (
        "progressive disclosure",
        "context capsule",
        "ChangeEnvelope",
    ),
}

SUITE_IDS = tuple(ADR_SKILLS.values())


def skill_text(skill_id: str) -> str:
    return (ROOT / "portable" / skill_id / "SKILL.md").read_text(encoding="utf-8")


def catalog_entry(skill_id: str) -> dict:
    for entry in CATALOG["skills"]:
        if entry["id"] == skill_id:
            return entry
    raise AssertionError(f"missing catalog entry: {skill_id}")


def long_paragraphs(text: str) -> set[str]:
    """Return normalised body paragraphs substantial enough to be copied."""
    body = text.split("---", 2)[-1]
    found = set()
    for block in re.split(r"\n\s*\n", body):
        normalised = " ".join(block.split())
        if len(normalised.split()) > 45:
            found.add(normalised)
    return found


class AdrSkillSuiteTests(unittest.TestCase):
    def test_mapping_is_one_skill_per_adr(self) -> None:
        self.assertEqual(len(ADR_SKILLS), 9)
        self.assertEqual(len(set(SUITE_IDS)), 9)
        for adr, skill_id in ADR_SKILLS.items():
            entry = catalog_entry(skill_id)
            self.assertEqual(entry["source_path"], f"portable/{skill_id}")
            self.assertIn(MERGE_REF, entry["provenance"]["adr"])
            self.assertIn(adr, entry["provenance"]["adr"])
            self.assertEqual(entry["provenance"]["issue"], ISSUE_REF)
            self.assertEqual(entry["version"], "1.0.0")
            self.assertEqual(set(entry["compatibility"]["runtimes"]), {
                "hermes",
                "codex",
                "droid",
            })
            self.assertFalse(entry["compatibility"]["network"])

    def test_no_other_catalog_entry_claims_suite_adrs(self) -> None:
        suite = set(ADR_SKILLS)
        for entry in CATALOG["skills"]:
            claimed = set(re.findall(r"ADR-00\d\d", entry["provenance"]["adr"]))
            if entry["id"] in SUITE_IDS:
                self.assertEqual(len(claimed), 1, entry["id"])
            else:
                self.assertFalse(
                    claimed & suite,
                    f"{entry['id']} claims a suite ADR: {sorted(claimed & suite)}",
                )

    def test_each_skill_states_its_source_decision(self) -> None:
        for adr, skill_id in ADR_SKILLS.items():
            text = skill_text(skill_id)
            self.assertIn(adr, text, skill_id)
            self.assertIn(MERGE_REF, text, skill_id)
            self.assertIn(MERGE_COMMIT, text, skill_id)
            self.assertEqual(text.count("## Source"), 1, skill_id)

    def test_required_sections_present(self) -> None:
        for skill_id in SUITE_IDS:
            text = skill_text(skill_id)
            for heading in REQUIRED_SECTIONS:
                self.assertEqual(text.count(heading), 1, f"{skill_id}: {heading}")
            self.assertIn("## Procedure", text, skill_id)

    def test_anti_patterns_and_checklist_are_operational(self) -> None:
        for skill_id in SUITE_IDS:
            text = skill_text(skill_id)
            wrong = text.count("**Wrong:**")
            right = text.count("**Right:**")
            self.assertGreaterEqual(wrong, 3, skill_id)
            self.assertEqual(wrong, right, skill_id)
            self.assertGreaterEqual(text.count("- [ ]"), 6, skill_id)

    def test_owned_content_is_present(self) -> None:
        for skill_id in SUITE_IDS:
            text = skill_text(skill_id)
            for token in OWNED_TOKENS[skill_id]:
                self.assertIn(token, text, f"{skill_id}: {token}")

    def test_skills_cross_reference_siblings_without_self_reference(self) -> None:
        for skill_id in SUITE_IDS:
            text = skill_text(skill_id)
            siblings = [other for other in SUITE_IDS if other != skill_id]
            referenced = [other for other in siblings if other in text]
            self.assertGreaterEqual(len(referenced), 2, skill_id)
            handoffs = text.split("## Handoffs", 1)[1].split("\n## ", 1)[0]
            self.assertNotIn(skill_id, handoffs, skill_id)

    def test_no_skill_duplicates_another_skill_body(self) -> None:
        seen: dict[str, str] = {}
        for skill_id in SUITE_IDS:
            for paragraph in long_paragraphs(skill_text(skill_id)):
                self.assertNotIn(
                    paragraph[:120],
                    seen,
                    f"{skill_id} duplicates a paragraph from {seen.get(paragraph[:120])}",
                )
                seen[paragraph[:120]] = skill_id

    def test_suite_content_is_public_safe(self) -> None:
        forbidden = (
            "/home/",
            "/Users/",
            "ghp_",
            "sk-",
            "xoxb-",
            "BEGIN RSA PRIVATE",
        )
        for skill_id in SUITE_IDS:
            text = skill_text(skill_id)
            for token in forbidden:
                self.assertNotIn(token, text, f"{skill_id}: {token}")

    def test_catalog_hash_tracks_every_skill_file(self) -> None:
        for skill_id in SUITE_IDS:
            files = sorted(
                path.relative_to(ROOT / "portable" / skill_id).as_posix()
                for path in (ROOT / "portable" / skill_id).rglob("*")
                if path.is_file()
            )
            self.assertEqual(files, ["SKILL.md"], skill_id)


if __name__ == "__main__":
    unittest.main()
