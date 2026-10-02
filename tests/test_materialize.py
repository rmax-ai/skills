from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import materialize  # noqa: E402


class MaterializeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "source"
        self.root.mkdir()
        shutil.copytree(ROOT / "portable", self.root / "portable")
        shutil.copytree(ROOT / "catalog", self.root / "catalog")
        (self.root / "profiles").mkdir()
        self.install_root = self.root.parent / "installed"
        self.profile = self.root / "profiles" / "fixture.json"
        self.profile.write_text(
            json.dumps(
                {
                    "id": "fixture",
                    "runtime": "codex",
                    "install_root": str(self.install_root),
                    "mode": "copy",
                }
            ),
            encoding="utf-8",
        )

    def test_hermes_home_placeholder_defaults_to_dot_hermes(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HERMES_HOME", None)
            resolved = materialize._resolve_install_root(
                {"install_root": "<HERMES_HOME>/skills/engineering"}, Path("profile.json")
            )
        self.assertEqual(
            resolved, Path.home() / ".hermes" / "skills" / "engineering"
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_tool(self, *flags: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = materialize.main(
                [
                    "--profile",
                    str(self.profile),
                    "--source",
                    str(self.root),
                    *flags,
                ]
            )
        return result, output.getvalue()

    def test_dry_run_is_deterministic(self) -> None:
        first_status, first_output = self.run_tool()
        second_status, second_output = self.run_tool()
        self.assertEqual(first_status, 0)
        self.assertEqual(second_status, 0)
        self.assertEqual(first_output, second_output)
        self.assertFalse(self.install_root.exists())

    def test_collision_refusal(self) -> None:
        status, _ = self.run_tool("--apply")
        self.assertEqual(status, 0)
        target = self.install_root / "pydantic-boundary-validation" / "SKILL.md"
        target.write_text("tampered\n", encoding="utf-8")
        status, output = self.run_tool("--apply")
        self.assertEqual(status, 1)
        self.assertIn("ERROR collision", output)

    def test_escape_refusal(self) -> None:
        outside = self.root.parent / "outside-install"
        outside.mkdir()
        if self.install_root.exists():
            self.install_root.rmdir()
        self.install_root.symlink_to(outside, target_is_directory=True)
        status, output = self.run_tool("--apply")
        self.assertEqual(status, 1)
        self.assertIn("ERROR symlink_escape", output)
        self.assertFalse((outside / "pydantic-boundary-validation").exists())

    def test_check_detects_drift(self) -> None:
        status, _ = self.run_tool("--apply")
        self.assertEqual(status, 0)
        target = self.install_root / "zod-boundary-validation" / "SKILL.md"
        target.write_text("drift\n", encoding="utf-8")
        status, output = self.run_tool("--check")
        self.assertEqual(status, 1)
        self.assertIn("ERROR drift", output)

    def test_apply_is_idempotent(self) -> None:
        first_status, first_output = self.run_tool("--apply")
        second_status, second_output = self.run_tool("--apply")
        self.assertEqual(first_status, 0)
        self.assertEqual(second_status, 0)
        self.assertEqual(first_output, second_output)
        for skill_id in ("pydantic-boundary-validation", "zod-boundary-validation"):
            self.assertTrue((self.install_root / skill_id / "SKILL.md").is_file())
