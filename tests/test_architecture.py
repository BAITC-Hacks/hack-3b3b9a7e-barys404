"""Guard module boundaries and paths during repository reorganizations."""
import ast
from pathlib import Path
import re

import pytest

from backend.core import config

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_paths_still_resolve_to_original_artifact_directories():
    assert config.ROOT == ROOT
    assert config.MODELS_DIR == ROOT / "models"
    assert config.ANALYTICAL_PATH == config.DATA_DIR / "processed" / "analytical.parquet"
    assert config.MODEL_PATH == ROOT / "models" / "waiting_time_catboost.cbm"
    from backend.api.main import DIST
    assert DIST == ROOT / "frontend" / "dist"


@pytest.mark.parametrize("package,forbidden", [
    ("backend/core", ("ml", "backend.api", "backend.legacy", "streamlit", "fastapi")),
    ("backend/api", ("backend.legacy", "streamlit")),
    ("backend/data_pipeline", ("backend.legacy", "backend.api", "streamlit", "fastapi")),
    ("ml", ("backend.api", "backend.legacy", "streamlit", "fastapi")),
])
def test_packages_do_not_import_presentation_or_transport_dependencies(package, forbidden):
    for path in (ROOT / package).rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = [item.name for item in node.names] if isinstance(node, ast.Import) else (
                [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            for name in names:
                assert not any(name == item or name.startswith(item + ".") for item in forbidden), (path, name)


def test_no_python_import_uses_the_removed_mixed_namespace():
    for directory in ("backend", "ml", "scripts", "tests"):
        for path in (ROOT / directory).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names = [item.name for item in node.names] if isinstance(node, ast.Import) else (
                    [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                assert not any(name == "src" or name.startswith("src.") for name in names), path


def test_local_documentation_links_survive_the_moves():
    documents = [ROOT / "README.md", *(ROOT / "docs").rglob("*.md"),
                 ROOT / "backend/README.md", ROOT / "frontend/README.md",
                 ROOT / "ml/README.md", ROOT / "models/README.md", ROOT / "scripts/README.md"]
    for path in documents:
        for destination in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if destination.startswith(("http:", "https:", "#", "mailto:")):
                continue
            target = destination.split("#", 1)[0]
            assert (path.parent / target).exists(), (path.relative_to(ROOT), target)
