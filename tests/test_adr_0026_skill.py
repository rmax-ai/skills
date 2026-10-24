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


SKILL_ID = "probabilistic-agent-evaluation"
SOURCE_PATH = "portable/probabilistic-agent-evaluation"
SKILL_DIR = ROOT / SOURCE_PATH
SKILL_TEXT = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
CATALOG = json.loads(
    (ROOT / "catalog" / "skills.json").read_text(encoding="utf-8")
)
REQUIRED_HEADINGS = (
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
REQUIRED_TERMS = (
    "variance",
    "sample size",
    "pass rate",
    "judge calibration",
    "seeded",
    "single run",
)
PUBLIC_SAFETY_MARKERS = (
    "/home/",
    "/Users/",
    "ghp_",
    "sk-",
    "xoxb-",
    "BEGIN RSA PRIVATE",
)


class ProbabilisticAgentEvaluationSkillTests(unittest.TestCase):
    def skill_entries(self) -> list[dict]:
        return [
            entry for entry in CATALOG["skills"] if entry["id"] == SKILL_ID
        ]

    def test_catalog_entry_matches_contract(self) -> None:
        entries = self.skill_entries()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["source_path"], SOURCE_PATH)
        self.assertEqual(entry["version"], "1.0.0")
        self.assertEqual(
            entry["provenance"]["issue"], "rmax-ai/delegation-queue#224"
        )
        self.assertIn("ADR-0026", entry["provenance"]["adr"])
        self.assertEqual(
            set(entry["compatibility"]["runtimes"]),
            {"hermes", "codex", "droid"},
        )
        self.assertIs(entry["compatibility"]["network"], False)

    def test_catalog_hash_matches_skill_sources(self) -> None:
        entry = self.skill_entries()[0]
        expected = catalog_check.source_hash(SKILL_DIR, ROOT / "portable")
        self.assertEqual(entry["source_hash"], expected)

    def test_skill_names_adr_and_decision_file(self) -> None:
        self.assertIn("ADR-0026", SKILL_TEXT)
        self.assertIn(
            "decisions/0026-probabilistic-evaluation-for-agentic-software-development-at-scale.md",
            SKILL_TEXT,
        )

    def test_required_headings_appear_once_in_order(self) -> None:
        for heading in REQUIRED_HEADINGS:
            with self.subTest(heading=heading):
                self.assertEqual(SKILL_TEXT.count(heading), 1)
        positions = [SKILL_TEXT.index(heading) for heading in REQUIRED_HEADINGS]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("## Procedure", SKILL_TEXT)

    def test_anti_patterns_have_matching_wrong_and_right_lines(self) -> None:
        wrong_count = SKILL_TEXT.count("**Wrong:**")
        right_count = SKILL_TEXT.count("**Right:**")
        self.assertGreaterEqual(wrong_count, 3)
        self.assertEqual(wrong_count, right_count)

    def test_verification_checklist_has_enough_items(self) -> None:
        self.assertGreaterEqual(SKILL_TEXT.count("- [ ]"), 6)

    def test_required_domain_terms_are_present(self) -> None:
        for term in REQUIRED_TERMS:
            with self.subTest(term=term):
                self.assertIn(term, SKILL_TEXT)

    def test_skill_has_no_public_safety_markers(self) -> None:
        for marker in PUBLIC_SAFETY_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, SKILL_TEXT)

    def test_skill_references_other_catalog_skills(self) -> None:
        other_ids = {
            entry["id"] for entry in CATALOG["skills"] if entry["id"] != SKILL_ID
        }
        referenced = {skill_id for skill_id in other_ids if skill_id in SKILL_TEXT}
        self.assertGreaterEqual(len(referenced), 2)


if __name__ == "__main__":
    unittest.main()
