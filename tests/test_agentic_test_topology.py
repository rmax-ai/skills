from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = "agentic-test-topology"
SKILL_PATH = ROOT / "portable" / SKILL_ID / "SKILL.md"
SKILL_TEXT = SKILL_PATH.read_text(encoding="utf-8")
CATALOG = json.loads(
    (ROOT / "catalog" / "skills.json").read_text(encoding="utf-8")
)
SOURCE_URL = (
    "https://github.com/rmax-ai/architecture/blob/main/decisions/"
    "0025-agentic-test-ownership-placement-and-execution-topology.md"
)


class AgenticTestTopologyTests(unittest.TestCase):
    def test_catalog_has_one_adr_0025_skill_with_task_provenance(self) -> None:
        entries = [
            entry
            for entry in CATALOG["skills"]
            if "ADR-0025" in entry["provenance"]["adr"]
        ]
        self.assertEqual([entry["id"] for entry in entries], [SKILL_ID])
        entry = entries[0]
        self.assertEqual(entry["source_path"], f"portable/{SKILL_ID}")
        self.assertEqual(
            entry["provenance"]["issue"],
            "rmax-ai/delegation-queue#216",
        )
        self.assertEqual(entry["version"], "1.0.0")
        self.assertEqual(
            set(entry["compatibility"]["runtimes"]),
            {"hermes", "codex", "droid"},
        )
        self.assertFalse(entry["compatibility"]["network"])

    def test_source_and_verification_sufficiency_handoff_are_explicit(self) -> None:
        self.assertIn("ADR-0025", SKILL_TEXT)
        self.assertIn(SOURCE_URL, SKILL_TEXT)
        self.assertIn("rmax-ai/delegation-queue#216", SKILL_TEXT)
        self.assertIn("ADR-0023", SKILL_TEXT)
        self.assertIn("claim-driven verification sufficiency", SKILL_TEXT)
        self.assertNotIn("ADR-0024", SKILL_TEXT)

    def test_ownership_hierarchy_is_explicit(self) -> None:
        for phrase in (
            "module behavioral tests",
            "nearest common owner",
            "repo boundary",
            "system boundary",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, SKILL_TEXT)

    def test_fixtures_contracts_relocation_and_affected_execution_are_covered(
        self,
    ) -> None:
        for phrase in (
            "fixture ownership",
            "reusable contract suite",
            "Move tests with their owner",
            "Move module behavioral tests and module-owned fixtures together",
            "Expand affected-target execution",
            "direct or transitive consumers",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, SKILL_TEXT)

    def test_layout_and_decision_procedure_are_concrete(self) -> None:
        for phrase in (
            "## Decision procedure",
            "## Repository layout example",
            "packages/inventory/",
            "packages/order-flow/tests/capabilities/",
            "tests/contracts/",
            "acceptance-harness/scenarios/",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, SKILL_TEXT)

    def test_independent_harness_criteria_and_anti_patterns_are_explicit(
        self,
    ) -> None:
        self.assertIn("## Independent black-box harness criteria", SKILL_TEXT)
        self.assertIn("without importing private implementation code", SKILL_TEXT)
        self.assertIn("mirrored `src/` and root `tests/` trees", SKILL_TEXT)
        self.assertIn("giant global fixture registry", SKILL_TEXT)
        self.assertIn("implementation-coupled tests", SKILL_TEXT)
        self.assertIn("implementation-specific tests", SKILL_TEXT)
        self.assertGreaterEqual(SKILL_TEXT.count("**Wrong:**"), 3)
        self.assertEqual(
            SKILL_TEXT.count("**Wrong:**"),
            SKILL_TEXT.count("**Right:**"),
        )

    def test_required_operational_sections_are_present(self) -> None:
        for heading in (
            "## Source",
            "## Purpose",
            "## When to use",
            "## Decision procedure",
            "## Invariants",
            "## Anti-patterns",
            "## Verification checklist",
            "## Failure and escalation",
            "## Handoffs",
        ):
            with self.subTest(heading=heading):
                self.assertEqual(SKILL_TEXT.count(heading), 1)
        self.assertGreaterEqual(SKILL_TEXT.count("- [ ]"), 6)

    def test_skill_tree_is_single_file_and_public_safe(self) -> None:
        files = sorted(
            path.relative_to(SKILL_PATH.parent).as_posix()
            for path in SKILL_PATH.parent.rglob("*")
            if path.is_file()
        )
        self.assertEqual(files, ["SKILL.md"])
        for marker in (
            "/home/",
            "/Users/",
            "ghp_",
            "sk-",
            "xoxb-",
            "BEGIN RSA PRIVATE",
        ):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, SKILL_TEXT)
        self.assertIsNone(
            re.search(r"(?i)(?:password|api[_ -]?key)\s*[:=]", SKILL_TEXT)
        )


if __name__ == "__main__":
    unittest.main()
