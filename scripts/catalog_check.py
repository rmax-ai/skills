#!/usr/bin/env python3
"""Validate the public skill catalog and compute deterministic source hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "skills.json"
PRIVATE_MARKERS = (
    re.compile(r"\b(?:INTERNAL|PRIVATE)[_ -]?(?:ONLY|MARKER)(?:\b|_)", re.IGNORECASE),
    re.compile(r"\b(?:DO[_ -]?NOT[_ -]?(?:PUBLISH|SHARE)|CONFIDENTIAL)\b", re.IGNORECASE),
    re.compile(r"BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY", re.IGNORECASE),
    re.compile(r"\b(?:api[_ -]?key|password|secret|access[_ -]?token)\s*[:=]\s*['\"]?[A-Za-z0-9+/=_-]{12,}", re.IGNORECASE),
    re.compile(r"(?:^|[/\\])(?:home|users)[/\\][A-Za-z0-9._-]+", re.IGNORECASE),
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RUNTIME_VALUES = {"hermes", "codex", "droid"}
TOP_LEVEL_KEYS = {"schema_version", "catalog_version", "skills", "hash_rule"}
SKILL_KEYS = {
    "id",
    "name",
    "description",
    "owner",
    "source_path",
    "source_hash",
    "compatibility",
    "version",
    "provenance",
}
COMPATIBILITY_KEYS = {"runtimes", "required_capabilities", "network"}
PROVENANCE_KEYS = {"adr", "issue"}


class CatalogError(ValueError):
    """A validation error with a stable machine-readable code."""

    def __init__(self, code: str, path: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.path = path
        self.message = message


def _error(code: str, path: str, message: str) -> CatalogError:
    return CatalogError(code, path, message)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _safe_file_bytes(path: Path, allowed_root: Path) -> bytes:
    try:
        resolved = path.resolve(strict=True)
        allowed_resolved = allowed_root.resolve(strict=True)
    except OSError as exc:
        raise _error("path_error", path.as_posix(), str(exc)) from exc
    if not _is_within(resolved, allowed_resolved):
        raise _error(
            "symlink_escape",
            path.as_posix(),
            "symlink resolves outside the allowed portable tree",
        )
    if not resolved.is_file():
        raise _error("not_a_file", path.as_posix(), "source entry is not a file")
    try:
        return resolved.read_bytes()
    except OSError as exc:
        raise _error("read_error", path.as_posix(), str(exc)) from exc


def iter_source_files(source_dir: Path, allowed_root: Path | None = None) -> list[tuple[str, Path]]:
    """Return source files as sorted ``(POSIX relative path, path)`` pairs.

    Symlinks are permitted only when they resolve inside ``allowed_root``.
    Directory symlinks are not followed, which keeps traversal deterministic
    and prevents cycles.
    """

    requested_source = Path(source_dir)
    try:
        source_dir = requested_source.resolve(strict=True)
        allowed = (allowed_root or requested_source.parent).resolve(strict=True)
    except OSError as exc:
        raise _error("source_missing", requested_source.as_posix(), str(exc)) from exc
    if not source_dir.is_dir():
        raise _error("source_missing", source_dir.as_posix(), "source path is not a directory")
    if not _is_within(source_dir, allowed):
        raise _error("path_escape", source_dir.as_posix(), "source is outside the allowed root")

    found: list[tuple[str, Path]] = []
    pending = [source_dir]
    seen_dirs: set[Path] = set()
    while pending:
        current = pending.pop()
        try:
            current_resolved = current.resolve(strict=True)
        except OSError as exc:
            raise _error("path_error", current.as_posix(), str(exc)) from exc
        if current_resolved in seen_dirs:
            continue
        seen_dirs.add(current_resolved)
        if not _is_within(current_resolved, allowed):
            raise _error(
                "symlink_escape",
                current.as_posix(),
                "directory symlink resolves outside the allowed root",
            )
        try:
            children = sorted(current.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise _error("read_error", current.as_posix(), str(exc)) from exc
        for child in children:
            try:
                child_resolved = child.resolve(strict=True)
            except OSError as exc:
                raise _error("path_error", child.as_posix(), str(exc)) from exc
            if not _is_within(child_resolved, allowed):
                raise _error(
                    "symlink_escape",
                    child.as_posix(),
                    "symlink or path resolves outside the allowed root",
                )
            if child.is_symlink() and child_resolved.is_dir():
                # Internal directory links are safe but are deliberately not
                # traversed, because the source hash is a tree, not a graph.
                continue
            if child_resolved.is_dir():
                pending.append(child)
            elif child_resolved.is_file():
                rel = child.relative_to(source_dir).as_posix()
                found.append((rel, child))
            else:
                raise _error("unsupported_entry", child.as_posix(), "source contains a non-file entry")
    return sorted(found, key=lambda item: item[0])


def source_hash(source_dir: Path, allowed_root: Path | None = None) -> str:
    """Compute the catalog hash for a source directory."""

    lines: list[str] = []
    allowed = allowed_root or Path(source_dir).parent.resolve()
    for relative, path in iter_source_files(source_dir, allowed):
        digest = hashlib.sha256(_safe_file_bytes(path, allowed)).hexdigest()
        lines.append(f"{relative} {digest}\n")
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _error("invalid_json", path.as_posix(), str(exc)) from exc


def _require_mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _error("schema_type", path, "expected an object")
    return value


def _require_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise _error("schema_type", path, "expected a non-empty string")
    return value


def _check_keys(value: dict[str, Any], expected: set[str], path: str) -> None:
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown:
        raise _error("schema_field", path, f"unknown field(s): {', '.join(unknown)}")
    if missing:
        raise _error("schema_field", path, f"missing field(s): {', '.join(missing)}")


def _scan_private_markers(source_dir: Path, files: Iterable[tuple[str, Path]], allowed_root: Path) -> None:
    for relative, path in files:
        try:
            text = _safe_file_bytes(path, allowed_root).decode("utf-8")
        except UnicodeDecodeError:
            continue
        for marker in PRIVATE_MARKERS:
            if marker.search(relative) or marker.search(text):
                raise _error(
                    "private_marker",
                    f"{source_dir.as_posix()}/{relative}",
                    "source contains a private or credential-shaped marker",
                )


def validate_catalog(root: Path = ROOT, catalog_path: Path | None = None) -> list[dict[str, Any]]:
    """Validate a catalog and return its skill entries."""

    catalog_path = catalog_path or root / "catalog" / "skills.json"
    document = _require_mapping(_read_json(catalog_path), "catalog")
    try:
        catalog_text = catalog_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise _error("read_error", catalog_path.as_posix(), str(exc)) from exc
    for marker in PRIVATE_MARKERS:
        if marker.search(catalog_text):
            raise _error(
                "private_marker",
                catalog_path.as_posix(),
                "catalog contains a private or credential-shaped marker",
            )
    _check_keys(document, TOP_LEVEL_KEYS, "catalog")
    if document["schema_version"] != 1:
        raise _error("schema_enum", "catalog.schema_version", "must be 1")
    _require_string(document["catalog_version"], "catalog.catalog_version")
    hash_rule = _require_string(document["hash_rule"], "catalog.hash_rule")
    expected_rule = (
        "source_hash = sha256 over sorted lines '<posix_relpath> "
        "<sha256(file_hex)>\\n' for all files under source_path, sorted by relpath"
    )
    if hash_rule != expected_rule:
        raise _error("schema_enum", "catalog.hash_rule", "does not match the supported hash rule")
    skills = document["skills"]
    if not isinstance(skills, list) or not skills:
        raise _error("schema_type", "catalog.skills", "expected a non-empty array")

    try:
        root_resolved = root.resolve(strict=True)
        portable_path = root / "portable"
        portable_root = portable_path.resolve(strict=True)
    except OSError as exc:
        raise _error("source_missing", (root / "portable").as_posix(), str(exc)) from exc
    if not _is_within(portable_root, root_resolved):
        raise _error("path_escape", "portable", "portable/ resolves outside the repository root")
    ids: set[str] = set()
    names: set[str] = set()
    for index, raw_skill in enumerate(skills):
        path = f"catalog.skills[{index}]"
        skill = _require_mapping(raw_skill, path)
        _check_keys(skill, SKILL_KEYS, path)
        skill_id = _require_string(skill["id"], f"{path}.id")
        skill_name = _require_string(skill["name"], f"{path}.name")
        _require_string(skill["description"], f"{path}.description")
        id_path = Path(skill_id)
        if (
            id_path.is_absolute()
            or id_path.name != skill_id
            or skill_id in {".", ".."}
        ):
            raise _error("path_escape", f"{path}.id", "must be a single safe path segment")
        owner = _require_string(skill["owner"], f"{path}.owner")
        if owner != "rmax-ai":
            raise _error("schema_enum", f"{path}.owner", "must be rmax-ai")
        if skill_id in ids:
            raise _error("duplicate_id", f"{path}.id", f"duplicate id: {skill_id}")
        if skill_name in names:
            raise _error("duplicate_name", f"{path}.name", f"duplicate name: {skill_name}")
        ids.add(skill_id)
        names.add(skill_name)
        source_path = _require_string(skill["source_path"], f"{path}.source_path")
        pure_source = Path(source_path)
        if pure_source.is_absolute() or ".." in pure_source.parts:
            raise _error("path_escape", f"{path}.source_path", "absolute and parent paths are forbidden")
        if pure_source.parts[:1] != ("portable",):
            raise _error("path_escape", f"{path}.source_path", "source must be under portable/")
        source_dir = root / pure_source
        try:
            resolved_source = source_dir.resolve(strict=True)
        except OSError as exc:
            raise _error("source_missing", source_path, str(exc)) from exc
        if not _is_within(resolved_source, portable_root) or not resolved_source.is_dir():
            raise _error("path_escape", source_path, "source resolves outside portable/")

        source_hash_value = _require_string(skill["source_hash"], f"{path}.source_hash")
        if not SHA256_RE.fullmatch(source_hash_value):
            raise _error("schema_format", f"{path}.source_hash", "must be a lowercase SHA-256 hex digest")
        files = iter_source_files(resolved_source, portable_root)
        if not any(relative == "SKILL.md" for relative, _ in files):
            raise _error("source_field", source_path, "source must contain SKILL.md")
        _scan_private_markers(resolved_source, files, portable_root)
        actual_hash = source_hash(resolved_source, portable_root)
        if actual_hash != source_hash_value:
            raise _error(
                "hash_mismatch",
                f"{path}.source_hash",
                f"catalog={source_hash_value} actual={actual_hash}",
            )

        compatibility = _require_mapping(skill["compatibility"], f"{path}.compatibility")
        _check_keys(compatibility, COMPATIBILITY_KEYS, f"{path}.compatibility")
        runtimes = compatibility["runtimes"]
        if (
            not isinstance(runtimes, list)
            or not runtimes
            or any(runtime not in RUNTIME_VALUES for runtime in runtimes)
            or len(set(runtimes)) != len(runtimes)
        ):
            raise _error("schema_enum", f"{path}.compatibility.runtimes", "contains invalid or duplicate runtimes")
        required = compatibility["required_capabilities"]
        if (
            not isinstance(required, list)
            or not required
            or any(not isinstance(capability, str) or not capability for capability in required)
        ):
            raise _error("schema_type", f"{path}.compatibility.required_capabilities", "must be non-empty strings")
        if not isinstance(compatibility["network"], bool):
            raise _error("schema_type", f"{path}.compatibility.network", "must be boolean")
        version = _require_string(skill["version"], f"{path}.version")
        if version != "1.0.0":
            raise _error("schema_enum", f"{path}.version", "must be 1.0.0")
        provenance = _require_mapping(skill["provenance"], f"{path}.provenance")
        _check_keys(provenance, PROVENANCE_KEYS, f"{path}.provenance")
        _require_string(provenance["adr"], f"{path}.provenance.adr")
        _require_string(provenance["issue"], f"{path}.provenance.issue")
    return skills


def _format_error(exc: CatalogError) -> str:
    return f"ERROR {exc.code} {exc.path} {exc.message}"


def _run_hash(path: Path) -> int:
    try:
        digest = source_hash(path)
    except (CatalogError, OSError) as exc:
        if isinstance(exc, CatalogError):
            print(_format_error(exc), file=sys.stderr)
        else:
            print(f"ERROR path_error {path.as_posix()} {exc}", file=sys.stderr)
        return 1
    print(digest)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("check",), default="check")
    parser.add_argument("--hash", dest="hash_path", metavar="DIR")
    args = parser.parse_args(argv)
    if args.hash_path is not None:
        if args.command != "check":
            parser.error("--hash cannot be combined with a command")
        return _run_hash(Path(args.hash_path))
    try:
        skills = validate_catalog()
    except CatalogError as exc:
        print(_format_error(exc))
        return 1
    print(f"OK catalog skills={len(skills)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
