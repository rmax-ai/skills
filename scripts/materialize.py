#!/usr/bin/env python3
"""Plan, check, or safely copy catalogued skills into a profile root."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import catalog_check


class MaterializeError(ValueError):
    """A guarded materializer error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _error(code: str, message: str) -> MaterializeError:
    return MaterializeError(code, message)


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _error("invalid_json", f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise _error("schema_type", f"{path}: expected an object")
    return value


def _resolve_install_root(profile: dict[str, Any], profile_path: Path) -> Path:
    raw = profile.get("install_root")
    if not isinstance(raw, str) or not raw:
        raise _error("profile_field", f"{profile_path}: install_root must be a non-empty string")
    hermes_home = os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes")
    expanded = raw.replace("<HERMES_HOME>", hermes_home)
    # Keep the final path lexical so _safe_target_path can detect a symlinked
    # install root instead of resolving it away.
    return Path(os.path.abspath(os.fspath(Path(expanded).expanduser())))


def _load_profile(profile_path: Path) -> tuple[str, Path]:
    profile = _read_json(profile_path)
    if profile.get("mode") != "copy":
        raise _error("profile_enum", f"{profile_path}: mode must be copy")
    profile_id = profile.get("id")
    if not isinstance(profile_id, str) or not profile_id:
        raise _error("profile_field", f"{profile_path}: id must be a non-empty string")
    runtime = profile.get("runtime")
    if runtime not in catalog_check.RUNTIME_VALUES:
        raise _error("profile_enum", f"{profile_path}: unsupported runtime")
    return profile_id, _resolve_install_root(profile, profile_path)


def _safe_target_path(target: Path, install_root: Path) -> None:
    if not _within(target, install_root):
        raise _error("write_escape", f"target is outside install_root: {target}")
    current = Path(install_root.anchor)
    for part in install_root.parts[1:]:
        current /= part
        if current.is_symlink():
            raise _error("symlink_escape", f"path contains a symlink: {current}")
    relative_parts = target.relative_to(install_root).parts
    for part in relative_parts:
        current = current / part
        if current.is_symlink():
            raise _error("symlink_escape", f"target path contains a symlink: {current}")


def _file_digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise _error("read_error", f"{path}: {exc}") from exc


def _target_files(target_dir: Path, install_root: Path) -> dict[str, Path]:
    if target_dir.is_symlink():
        raise _error("symlink_escape", f"target directory is a symlink: {target_dir}")
    if not target_dir.exists():
        return {}
    if not target_dir.is_dir():
        raise _error("collision", f"target is not a directory: {target_dir}")
    result: dict[str, Path] = {}
    pending = [target_dir]
    while pending:
        current = pending.pop()
        _safe_target_path(current, install_root)
        for child in sorted(current.iterdir(), key=lambda item: item.name):
            _safe_target_path(child, install_root)
            if child.is_symlink():
                raise _error("symlink_escape", f"target contains a symlink: {child}")
            if child.is_dir():
                pending.append(child)
            elif child.is_file():
                result[child.relative_to(target_dir).as_posix()] = child
            else:
                raise _error("collision", f"target contains unsupported entry: {child}")
    return result


def _validate_catalog(source_root: Path) -> list[dict[str, Any]]:
    try:
        catalog_check.validate_catalog(source_root)
    except catalog_check.CatalogError as exc:
        raise _error(exc.code, f"{exc.path}: {exc.message}") from exc
    try:
        return _read_json(source_root / "catalog" / "skills.json")["skills"]
    except KeyError as exc:
        raise _error("schema_field", "catalog.skills is missing") from exc


def _build_manifest(source_root: Path, install_root: Path) -> tuple[list[dict[str, str]], list[Path]]:
    skills = _validate_catalog(source_root)
    portable_root = (source_root / "portable").resolve(strict=True)
    manifest: list[dict[str, str]] = []
    target_dirs: list[Path] = []
    for skill in skills:
        skill_id = skill["id"]
        if (
            not isinstance(skill_id, str)
            or not skill_id
            or Path(skill_id).is_absolute()
            or Path(skill_id).name != skill_id
            or skill_id in {".", ".."}
        ):
            raise _error("path_escape", f"invalid skill id for destination: {skill_id!r}")
        source_path = Path(skill["source_path"])
        source_dir = (source_root / source_path).resolve(strict=True)
        if not _within(source_dir, portable_root):
            raise _error("path_escape", f"source outside portable/: {source_path}")
        target_dir = install_root / skill_id
        if not _within(target_dir, install_root):
            raise _error("write_escape", f"destination outside install_root: {target_dir}")
        _safe_target_path(target_dir, install_root)
        target_dirs.append(target_dir)
        try:
            source_files = catalog_check.iter_source_files(source_dir, portable_root)
        except catalog_check.CatalogError as exc:
            raise _error(exc.code, f"{exc.path}: {exc.message}") from exc
        for relative, source_file in source_files:
            destination = target_dir / relative
            _safe_target_path(destination, install_root)
            try:
                digest = hashlib.sha256(
                    catalog_check._safe_file_bytes(source_file, portable_root)
                ).hexdigest()
            except catalog_check.CatalogError as exc:
                raise _error(exc.code, f"{exc.path}: {exc.message}") from exc
            manifest.append(
                {
                    "src": source_file.relative_to(source_root).as_posix(),
                    "dst": destination.as_posix(),
                    "sha256": digest,
                }
            )
    manifest.sort(key=lambda item: (item["dst"], item["src"]))
    return manifest, target_dirs


def _check_collisions(manifest: list[dict[str, str]], target_dirs: list[Path], install_root: Path, *, require_existing: bool) -> None:
    expected_by_dir: dict[Path, dict[str, str]] = {}
    for item in manifest:
        destination = Path(item["dst"])
        target_dir = next(
            (candidate for candidate in target_dirs if _within(destination, candidate)),
            None,
        )
        if target_dir is None:
            raise _error("write_escape", f"manifest destination is outside target dirs: {destination}")
        expected_by_dir.setdefault(target_dir, {})[
            destination.relative_to(target_dir).as_posix()
        ] = item["sha256"]

    for target_dir in target_dirs:
        existing = _target_files(target_dir, install_root)
        expected = expected_by_dir.get(target_dir, {})
        if not target_dir.exists():
            if require_existing:
                raise _error("drift", f"missing target directory: {target_dir}")
            continue
        if set(existing) != set(expected):
            raise _error(
                "collision" if not require_existing else "drift",
                f"target content differs: {target_dir}",
            )
        for relative, path in existing.items():
            if _file_digest(path) != expected[relative]:
                raise _error(
                    "collision" if not require_existing else "drift",
                    f"target file differs: {path}",
                )


def _print_manifest(manifest: list[dict[str, str]]) -> None:
    for item in manifest:
        print(json.dumps(item, sort_keys=True, separators=(",", ":")))


def materialize(profile_path: Path, source_root: Path, mode: str) -> int:
    source_root = source_root.resolve(strict=True)
    if not source_root.is_dir():
        raise _error("source_missing", f"source root is not a directory: {source_root}")
    _, install_root = _load_profile(profile_path.resolve(strict=True))
    manifest, target_dirs = _build_manifest(source_root, install_root)
    _check_collisions(
        manifest,
        target_dirs,
        install_root,
        require_existing=mode == "check",
    )
    _print_manifest(manifest)
    if mode == "dry-run":
        print(f"OK dry-run files={len(manifest)}")
        return 0
    if mode == "check":
        print(f"OK check files={len(manifest)}")
        return 0

    # All collision and symlink checks happen before the first write.
    for item in manifest:
        destination = Path(item["dst"])
        _safe_target_path(destination, install_root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            # The collision pass already proved this is the expected file.
            continue
        source_file = source_root / item["src"]
        shutil.copyfile(source_file, destination)
    print(f"OK apply files={len(manifest)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--check", action="store_true")
    mode_group.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    mode = "check" if args.check else "apply" if args.apply else "dry-run"
    try:
        return materialize(args.profile, args.source, mode)
    except (MaterializeError, OSError) as exc:
        if isinstance(exc, MaterializeError):
            print(f"ERROR {exc.code} {exc.message}")
        else:
            print(f"ERROR filesystem {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
