from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE_DIR = ROOT / "tests" / "probes" / "zod-variant-mapping"
PINNED_ZOD = "4.6.5"


class PinnedProbeTests(unittest.TestCase):
    """The manual probes are pinned to exact toolchains; keep the pins honest."""

    def test_zod_probe_pins_exact_version(self) -> None:
        manifest = json.loads(
            (PROBE_DIR / "package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["dependencies"], {"zod": PINNED_ZOD})
        script = (PROBE_DIR / "variant-mapping.mjs").read_text(encoding="utf-8")
        self.assertIn(f'const PINNED_ZOD = "{PINNED_ZOD}"', script)
        for token in (
            "invalid_union",
            "invalid_value",
            "input.variant",
            "input.invalid",
        ):
            self.assertIn(token, script)
        self.assertTrue((PROBE_DIR / "README.md").is_file())
        self.assertTrue((PROBE_DIR / ".gitignore").is_file())

    def test_zod_skill_references_pinned_probe(self) -> None:
        text = (
            ROOT / "portable" / "zod-boundary-validation" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("tests/probes/zod-variant-mapping/", text)


if __name__ == "__main__":
    unittest.main()
