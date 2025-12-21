#!/usr/bin/env python3
"""Shared helpers for plan scripts."""

from __future__ import annotations

import os
import re
from pathlib import Path

_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def find_git_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def get_project_root() -> Path:
    env_root = os.environ.get("CODEX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    git_root = find_git_root(Path.cwd())
    if git_root:
        return git_root

    raise SystemExit(
        "Unable to locate a git repo root. Run from within a repo or set "
        "CODEX_PROJECT_ROOT or CODEX_PLAN_DIR."
    )


def get_plans_dir() -> Path:
    explicit = os.environ.get("CODEX_PLAN_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()

    return get_project_root() / ".codex" / "plans"


def validate_plan_name(name: str) -> None:
    if not name or not _NAME_RE.match(name):
        raise ValueError(
            "Invalid plan name. Use short, lower-case, hyphen-delimited names "
            "(e.g., codex-rate-limit-overview)."
        )


def parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter from a markdown file without reading the body."""
    with path.open("r", encoding="utf-8") as handle:
        first = handle.readline()
        if first.strip() != "---":
            raise ValueError("Frontmatter must start with '---'.")

        data: dict[str, str] = {}
        for line in handle:
            stripped = line.strip()
            if stripped == "---":
                return data
            if not stripped or stripped.startswith("#"):
                continue
            if ":" not in line:
                raise ValueError(f"Invalid frontmatter line: {line.rstrip()}")
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value and len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            data[key] = value

    raise ValueError("Frontmatter must end with '---'.")
