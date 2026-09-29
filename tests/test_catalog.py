from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import catalog_check  # noqa: E402


class CatalogFixtureMixin:
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "catalog").mkdir()
        (self.root / "portable" / "example").mkdir(parents=True)
        self.skill_file = self.root / "portable" / "example" / "SKILL.md"
        self.skill_file.write_text(
            "---\nname: example\ndescription: A fixture skill.\n---\n\n# Example\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_catalog(self, **skill_changes: object) -> Path:
        source = "portable/example"
        digest = catalog_check.source_hash(self.root / source, self.root / "portable")
        skill: dict[str, object] = {
            "id": "example",
            "name": "Example",
            "description": "A fixture skill.",
            "owner": "rmax-ai",
            "source_path": source,
            "source_hash": digest,
            "compatibility": {
                "runtimes": ["hermes", "codex", "droid"],
                "required_capabilities": ["python>=3.10"],
                "network": False,
            },
            "version": "1.0.0",
            "provenance": {
                "adr": "rmax-ai/architecture#13",
                "issue": "rmax-ai/delegation-queue#105",
            },
        }
        skill.update(skill_changes)
        document = {
            "schema_version": 1,
            "catalog_version": "1.0.0",
            "skills": [skill],
            "hash_rule": (
                "source_hash = sha256 over sorted lines '<posix_relpath> "
                "<sha256(file_hex)>\\n' for all files under source_path, sorted by relpath"
            ),
        }
        catalog_path = self.root / "catalog" / "skills.json"
        catalog_path.write_text(json.dumps(document), encoding="utf-8")
        return catalog_path


class CatalogValidationTests(CatalogFixtureMixin, unittest.TestCase):
    def test_good_catalog_passes(self) -> None:
        self.write_catalog()
        self.assertEqual(len(catalog_check.validate_catalog(self.root)), 1)

    def test_tampered_hash_fails(self) -> None:
        self.write_catalog(source_hash="0" * 64)
        with self.assertRaises(catalog_check.CatalogError) as context:
            catalog_check.validate_catalog(self.root)
        self.assertEqual(context.exception.code, "hash_mismatch")

    def test_hash_drift_fixture_fails(self) -> None:
        fixture_root = ROOT / "tests" / "fixtures" / "hash-drift"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(fixture_root / "portable", root / "portable")
            source = root / "portable" / "example"
            digest = catalog_check.source_hash(source, root / "portable")
            document = {
                "schema_version": 1,
                "catalog_version": "1.0.0",
                "skills": [
                    {
                        "id": "example",
                        "name": "Example",
                        "description": "Fixture",
                        "owner": "rmax-ai",
                        "source_path": "portable/example",
                        "source_hash": digest,
                        "compatibility": {
                            "runtimes": ["hermes"],
                            "required_capabilities": ["python>=3.10"],
                            "network": False,
                        },
                        "version": "1.0.0",
                        "provenance": {
                            "adr": "rmax-ai/architecture#13",
                            "issue": "rmax-ai/delegation-queue#105",
                        },
                    }
                ],
                "hash_rule": (
                    "source_hash = sha256 over sorted lines '<posix_relpath> "
                    "<sha256(file_hex)>\\n' for all files under source_path, sorted by relpath"
                ),
            }
            (root / "catalog").mkdir()
            (root / "catalog" / "skills.json").write_text(
                json.dumps(document), encoding="utf-8"
            )
            (source / "SKILL.md").write_text(
                (source / "SKILL.md").read_text(encoding="utf-8") + "\nchanged\n",
                encoding="utf-8",
            )
            with self.assertRaises(catalog_check.CatalogError) as context:
                catalog_check.validate_catalog(root)
        self.assertEqual(context.exception.code, "hash_mismatch")

    def test_duplicate_id_fails(self) -> None:
        catalog_path = self.write_catalog()
        document = json.loads(catalog_path.read_text(encoding="utf-8"))
        duplicate = dict(document["skills"][0])
        duplicate["name"] = "Another name"
        document["skills"].append(duplicate)
        catalog_path.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(catalog_check.CatalogError) as context:
            catalog_check.validate_catalog(self.root)
        self.assertEqual(context.exception.code, "duplicate_id")

    def test_bad_enum_fails(self) -> None:
        self.write_catalog(
            compatibility={
                "runtimes": ["unknown-runtime"],
                "required_capabilities": ["python>=3.10"],
                "network": False,
            }
        )
        with self.assertRaises(catalog_check.CatalogError) as context:
            catalog_check.validate_catalog(self.root)
        self.assertEqual(context.exception.code, "schema_enum")

    def test_private_marker_fixture_fails(self) -> None:
        fixture_root = ROOT / "tests" / "fixtures" / "private-marker"
        portable = fixture_root / "portable"
        source = portable / "example"
        digest = catalog_check.source_hash(source, portable)
        catalog = {
            "schema_version": 1,
            "catalog_version": "1.0.0",
            "skills": [
                {
                    "id": "example",
                    "name": "Example",
                    "description": "Fixture",
                    "owner": "rmax-ai",
                    "source_path": "portable/example",
                    "source_hash": digest,
                    "compatibility": {
                        "runtimes": ["hermes"],
                        "required_capabilities": ["python>=3.10"],
                        "network": False,
                    },
                    "version": "1.0.0",
                    "provenance": {
                        "adr": "rmax-ai/architecture#13",
                        "issue": "rmax-ai/delegation-queue#105",
                    },
                }
            ],
            "hash_rule": (
                "source_hash = sha256 over sorted lines '<posix_relpath> "
                "<sha256(file_hex)>\\n' for all files under source_path, sorted by relpath"
            ),
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(portable, root / "portable")
            (root / "catalog").mkdir()
            (root / "catalog" / "skills.json").write_text(
                json.dumps(catalog), encoding="utf-8"
            )
            with self.assertRaises(catalog_check.CatalogError) as context:
                catalog_check.validate_catalog(root)
        self.assertEqual(context.exception.code, "private_marker")

    @unittest.skipUnless(hasattr(Path, "symlink_to"), "symlink support is unavailable")
    def test_symlink_escape_fixture_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            portable = root / "portable" / "example"
            portable.mkdir(parents=True)
            (portable / "SKILL.md").write_text(
                "---\nname: example\ndescription: Fixture\n---\n",
                encoding="utf-8",
            )
            outside = root / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            (portable / "escaped.txt").symlink_to(outside)
            (root / "catalog").mkdir()
            digest = "0" * 64
            catalog = {
                "schema_version": 1,
                "catalog_version": "1.0.0",
                "skills": [
                    {
                        "id": "example",
                        "name": "Example",
                        "description": "Fixture",
                        "owner": "rmax-ai",
                        "source_path": "portable/example",
                        "source_hash": digest,
                        "compatibility": {
                            "runtimes": ["hermes"],
                            "required_capabilities": ["python>=3.10"],
                            "network": False,
                        },
                        "version": "1.0.0",
                        "provenance": {
                            "adr": "rmax-ai/architecture#13",
                            "issue": "rmax-ai/delegation-queue#105",
                        },
                    }
                ],
                "hash_rule": (
                    "source_hash = sha256 over sorted lines '<posix_relpath> "
                    "<sha256(file_hex)>\\n' for all files under source_path, sorted by relpath"
                ),
            }
            (root / "catalog" / "skills.json").write_text(
                json.dumps(catalog), encoding="utf-8"
            )
            with self.assertRaises(catalog_check.CatalogError) as context:
                catalog_check.validate_catalog(root)
        self.assertEqual(context.exception.code, "symlink_escape")
