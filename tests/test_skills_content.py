from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads(
    (ROOT / "catalog" / "skills.json").read_text(encoding="utf-8")
)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError("frontmatter must start with ---")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError("frontmatter must close with ---") from exc
    fields: dict[str, str] = {}
    description_lines: list[str] = []
    in_description = False
    for line in lines[1:end]:
        if line == "description: >-":
            if "description" in fields:
                raise AssertionError("duplicate description")
            fields["description"] = ""
            in_description = True
            continue
        if in_description and (line.startswith("  ") or not line):
            description_lines.append(line.strip())
            continue
        in_description = False
        if ":" not in line:
            raise AssertionError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    if description_lines:
        fields["description"] = " ".join(part for part in description_lines if part)
    return fields, "\n".join(lines[end + 1 :])


class SkillContentTests(unittest.TestCase):
    def test_frontmatter_and_catalog_names(self) -> None:
        for entry in CATALOG["skills"]:
            path = ROOT / entry["source_path"] / "SKILL.md"
            fields, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            self.assertEqual(set(fields), {"name", "description"})
            self.assertEqual(fields["name"], entry["id"])
            self.assertGreaterEqual(len(fields["description"].split()), 10)
            self.assertTrue(body.lstrip().startswith("#"))

    def test_pydantic_required_content(self) -> None:
        text = (
            ROOT / "portable" / "pydantic-boundary-validation" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for token in (
            "model_validate",
            "model_validate_json",
            "model_json_schema",
            "TypeAdapter",
            "ConfigDict",
            "discriminator",
        ):
            self.assertIn(token, text)
        self.assertIn("## Domain error mapping", text)
        self.assertGreaterEqual(text.count("**Wrong:**"), 3)
        self.assertGreaterEqual(text.count("**Right:**"), 3)

    def test_zod_required_content(self) -> None:
        text = (
            ROOT / "portable" / "zod-boundary-validation" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for token in ("safeParse", "discriminatedUnion", "toJSONSchema", "strictObject"):
            self.assertIn(token, text)
        self.assertIn("## Domain error mapping", text)
        self.assertGreaterEqual(text.count("**Wrong:**"), 3)
        self.assertGreaterEqual(text.count("**Right:**"), 3)

    def test_skill_text_has_no_unfinished_or_private_markers(self) -> None:
        unfinished = ("TO" + "DO", "FIX" + "ME", "X" + "XX")
        private = ("INTERNAL" + "[_ -]?ONLY", "PRIVATE" + "[_ -]?ONLY")
        marker_pattern = re.compile(
            "|".join((*unfinished, *private)),
            re.IGNORECASE,
        )
        for entry in CATALOG["skills"]:
            skill_dir = ROOT / entry["source_path"]
            for path in sorted(skill_dir.rglob("*")):
                if path.is_file():
                    text = path.read_text(encoding="utf-8")
                    self.assertIsNone(marker_pattern.search(text), path.as_posix())
