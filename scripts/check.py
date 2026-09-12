#!/usr/bin/env python3
"""Single check entry point for fieldy-client.

Offline, deterministic, stdlib only. CI runs exactly this file, so a local
run and a CI run cannot disagree. Add mechanical rules here rather than to
the review rules in AGENTS.md.

Usage: python scripts/check.py
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

ROOT = Path(__file__).resolve().parent.parent

# Runtime code must import nothing outside the standard library (AGENTS.md,
# Working rules). Tests may use pytest; scripts/ is excluded as tooling.
RUNTIME_MODULES = ("fieldy_client.py", "smoke.py")

# Assignment of a key to a literal, tolerant of whitespace and of JSON/TOML
# spellings: FIELDY_API_KEY = "x", "FIELDY_API_KEY": "x", FIELDY_API_KEY=x.
KEY_ASSIGNMENT = re.compile(
    r"""FIELDY_API_KEY["']?\s*[:=]\s*(?P<value>[^\s,;)}\]]+)""", re.IGNORECASE
)
# The issued-key prefix is a positive signal wherever it appears with a body.
KEY_LITERAL = re.compile(r"sk-fieldy-[A-Za-z0-9_-]{8,}")
# Values that are obviously not a key: placeholders and environment lookups.
NOT_A_KEY = re.compile(
    r"^(<|\$|\{|os\.|getenv|environ|none|null|\.\.\.|\u2026)|"
    r"(your|example|placeholder|dummy|fake|xxx|test)",
    re.IGNORECASE,
)
# An issued key is long. A short literal is prose or a placeholder, not a
# credential; the prefix rule above catches real keys whatever their spelling.
MIN_KEY_LENGTH = 12


def report(name: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {name}{': ' + detail if detail else ''}")
    return ok


def tracked_files() -> list[Path]:
    """Files git knows about, so untracked scratch work never fails a check."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return sorted(p for p in ROOT.rglob("*") if p.is_file())
    return [ROOT / name for name in out.split("\0") if name]


def check_python_parses(files: list[Path]) -> bool:
    bad = []
    for path in files:
        if path.suffix != ".py" or not path.exists():
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            bad.append(f"{path.relative_to(ROOT)}:{exc.lineno} {exc.msg}")
    return report("python parses", not bad, "; ".join(bad))


def check_stdlib_only(files: list[Path]) -> bool:
    """Enforce the no-runtime-dependency rule mechanically."""
    offenders = []
    for path in files:
        if path.name not in RUNTIME_MODULES or not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue  # reported by check_python_parses
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module] if node.level == 0 and node.module else []
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top and top not in sys.stdlib_module_names:
                    offenders.append(f"{path.relative_to(ROOT)} imports {top}")
    return report("runtime imports are stdlib only", not offenders, "; ".join(offenders))


def check_fixtures_parse(files: list[Path]) -> bool:
    bad = []
    for path in files:
        if path.suffix != ".json" or "fixtures" not in path.parts or not path.exists():
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            bad.append(f"{path.relative_to(ROOT)}: {exc}")
    return report("fixtures are valid JSON", not bad, "; ".join(bad))


def check_no_committed_key(files: list[Path]) -> bool:
    """A recorded key is the one mistake here that cannot be quietly undone."""
    offenders = []
    for path in files:
        if not path.exists() or path.name == Path(__file__).name:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            hit = None
            if KEY_LITERAL.search(line):
                hit = "issued-key prefix with a body"
            else:
                match = KEY_ASSIGNMENT.search(line)
                if match:
                    value = match.group("value").strip("\"'`")
                    if len(value) >= MIN_KEY_LENGTH and not NOT_A_KEY.search(value):
                        hit = "key assigned to a literal"
            if hit:
                offenders.append(f"{path.relative_to(ROOT)}:{lineno} {hit}")
                break
    return report("no API key in a tracked file", not offenders, "; ".join(offenders))


def check_declared_dependencies() -> bool:
    """Imports are only half the surface; installing must pull nothing either."""
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        return report("declared dependencies", True, "no pyproject.toml yet")
    if tomllib is None:
        return report("declared dependencies", True, "needs Python 3.11+ to parse")
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        return report("declared dependencies", False, f"pyproject.toml: {exc}")

    offenders = []
    project = data.get("project", {})
    for dep in project.get("dependencies", []):
        offenders.append(f"runtime dependency {dep!r}")
    groups = dict(project.get("optional-dependencies", {}))
    groups.update(data.get("dependency-groups", {}))
    for group, deps in groups.items():
        for dep in deps:
            if not str(dep).lower().startswith("pytest"):
                offenders.append(f"{group} dependency {dep!r}")
    return report("declared dependencies", not offenders, "; ".join(offenders))


def run_pytest() -> bool:
    tests = sorted((ROOT / "tests").glob("test_*.py")) if (ROOT / "tests").is_dir() else []
    if not tests:
        return report("tests", True, "no tests yet (scaffold)")
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
    return report("tests", proc.returncode == 0, f"pytest exit {proc.returncode}")


def main() -> int:
    files = tracked_files()
    results = [
        check_python_parses(files),
        check_stdlib_only(files),
        check_fixtures_parse(files),
        check_no_committed_key(files),
        check_declared_dependencies(),
        run_pytest(),
    ]
    ok = all(results)
    print("\nall checks passed" if ok else "\nchecks failed")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
