from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import catalog_check  # noqa: E402


SKILL_ID = "claim-driven-software-verification"
SKILL_DIR = ROOT / "portable" / SKILL_ID
SKILL_PATH = SKILL_DIR / "SKILL.md"
CATALOG_PATH = ROOT / "catalog" / "skills.json"
REQUIRED_TERMS = (
    "verification obligation",
    "evidence ladder",
    "affected scope",
    "residual risk",
    "fail closed",
)
HEADINGS = (
    "## Source",
    "## Purpose",
    "## When to use",
    "## Procedure",
    "## Invariants",
    "## Anti-patterns",
    "## Verification checklist",
    "## Failure and escalation",
    "## Handoffs",
)


class ADR0023SkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.skill_text = SKILL_PATH.read_text(encoding="utf-8")
        cls.entries = [
            skill for skill in cls.catalog["skills"] if skill["id"] == SKILL_ID
        ]

    def test_catalog_entry(self) -> None:
        self.assertEqual(len(self.entries), 1)
        entry = self.entries[0]
        self.assertEqual(
            entry["source_path"], "portable/claim-driven-software-verification"
        )
        self.assertEqual(entry["version"], "1.0.0")
        self.assertEqual(entry["provenance"]["issue"], "rmax-ai/delegation-queue#223")
        self.assertIn("ADR-0023", entry["provenance"]["adr"])
        self.assertEqual(set(entry["compatibility"]["runtimes"]), {"hermes", "codex", "droid"})
        self.assertIs(entry["compatibility"]["network"], False)

    def test_catalog_hash_matches_skill_directory(self) -> None:
        entry = self.entries[0]
        expected = catalog_check.source_hash(SKILL_DIR, ROOT / "portable")
        self.assertEqual(entry["source_hash"], expected)

    def test_source_and_required_headings(self) -> None:
        self.assertIn("ADR-0023", self.skill_text)
        self.assertIn(
            "decisions/0023-claim-driven-software-verification-for-agentic-development.md",
            self.skill_text,
        )
        self.assertIn("## Procedure", self.skill_text)
        for heading in HEADINGS:
            with self.subTest(heading=heading):
                self.assertEqual(self.skill_text.count(heading), 1)

    def test_paired_antipatterns_and_checklist(self) -> None:
        self.assertGreaterEqual(self.skill_text.count("**Wrong:**"), 3)
        self.assertEqual(
            self.skill_text.count("**Wrong:**"), self.skill_text.count("**Right:**")
        )
        self.assertGreaterEqual(self.skill_text.count("- [ ]"), 6)

    def test_domain_terms_and_public_safety(self) -> None:
        for term in REQUIRED_TERMS:
            with self.subTest(term=term):
                self.assertIn(term, self.skill_text)
        for marker in ("/home/", "/Users/", "ghp_", "sk-", "xoxb-", "BEGIN RSA PRIVATE"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.skill_text)

    def test_references_other_catalog_skills(self) -> None:
        catalog_ids = {skill["id"] for skill in self.catalog["skills"]}
        referenced = {
            skill_id
            for skill_id in ("agentic-verification-ladder", "change-envelope-planning")
            if skill_id in catalog_ids and skill_id in self.skill_text
        }
        self.assertGreaterEqual(len(referenced), 2)


if __name__ == "__main__":
    unittest.main()
