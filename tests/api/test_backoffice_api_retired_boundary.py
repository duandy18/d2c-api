from __future__ import annotations

from pathlib import Path

ACTIVE_PATHS = [
    Path("Makefile"),
    Path("scripts"),
    Path("app"),
    Path("tests"),
    Path("README.md"),
]

BOUNDARY_TEST_PATH = Path("tests/api/test_backoffice_api_retired_boundary.py")


def _token(*parts: str) -> str:
    return "".join(parts)


FORBIDDEN_TOKENS = [
    _token("D2C_", "BACKOFFICE_", "API_BASE_URL"),
    _token("http://127.0.0.1:", "8026"),
    _token("/api/", "d2c-backoffice"),
    _token("d2c-", "backoffice-api"),
    _token("sync-published-", "client-presentation"),
    _token("sync-published-", "snapshot-all"),
    _token("scripts/published/", "sync_published.py"),
]


def _iter_active_files() -> list[Path]:
    files: list[Path] = []
    for root in ACTIVE_PATHS:
        if not root.exists():
            continue

        if root.is_file():
            if root != BOUNDARY_TEST_PATH:
                files.append(root)
            continue

        for path in root.rglob("*"):
            if path == BOUNDARY_TEST_PATH:
                continue
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if ".pytest_cache" in path.parts:
                continue
            if path.suffix in {"", ".py", ".md"} or path.name == "Makefile":
                files.append(path)

    return files


def test_backoffice_api_active_sync_surface_is_retired() -> None:
    assert not Path("scripts/published/sync_published.py").exists()
    assert not Path("tests/api/test_published_snapshot_sync.py").exists()
    assert not Path("tests/api/test_published_sync.py").exists()

    offenders: list[str] = []
    for path in _iter_active_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in FORBIDDEN_TOKENS:
            if token in text:
                offenders.append(f"{path}:{token}")

    assert offenders == []
