"""Every module under app/ must compile (catches SyntaxErrors before startup)."""

import ast
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parent.parent / "app"
PY_FILES = sorted(APP_DIR.rglob("*.py"))


def test_app_files_found():
    assert PY_FILES


@pytest.mark.parametrize("path", PY_FILES, ids=lambda p: str(p.relative_to(APP_DIR)))
def test_module_compiles(path):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
