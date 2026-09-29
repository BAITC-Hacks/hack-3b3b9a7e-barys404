"""Guard module boundaries and paths during repository reorganizations."""

import ast
import re
from pathlib import Path

import pytest

from backend.core import config

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_paths_still_resolve_to_original_artifact_directories():
    assert config.ROOT == ROOT
    assert config.MODELS_DIR == ROOT / "models"
    assert (
        config.ANALYTICAL_PATH == config.DATA_DIR / "processed" / "analytical.parquet"
    )
    assert config.MODEL_PATH == ROOT / "models" / "waiting_time_catboost.cbm"
    from backend.http.frontend import DIST

    assert DIST == ROOT / "frontend" / "dist"


@pytest.mark.parametrize(
    "package,forbidden",
    [
        (
            "backend/core",
            (
                "ml",
                "backend.modules",
                "backend.http",
                "backend.main",
                "backend.legacy",
                "streamlit",
                "fastapi",
            ),
        ),
        ("backend/modules", ("backend.legacy", "streamlit")),
        ("backend/http", ("backend.legacy", "streamlit")),
        (
            "backend/data_pipeline",
            (
                "backend.legacy",
                "backend.modules",
                "backend.http",
                "backend.main",
                "streamlit",
                "fastapi",
            ),
        ),
        (
            "ml",
            (
                "backend.modules",
                "backend.http",
                "backend.main",
                "backend.legacy",
                "streamlit",
                "fastapi",
            ),
        ),
    ],
)
def test_packages_do_not_import_presentation_or_transport_dependencies(
    package, forbidden
):
    for path in (ROOT / package).rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [item.name for item in node.names]
                if isinstance(node, ast.Import)
                else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            )
            for name in names:
                assert not any(
                    name == item or name.startswith(item + ".") for item in forbidden
                ), (path, name)


def test_no_python_import_uses_the_removed_mixed_namespace():
    for directory in ("backend", "ml", "scripts", "tests"):
        for path in (ROOT / directory).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names = (
                    [item.name for item in node.names]
                    if isinstance(node, ast.Import)
                    else (
                        [node.module or ""] if isinstance(node, ast.ImportFrom) else []
                    )
                )
                assert not any(
                    name == prefix or name.startswith(prefix + ".")
                    for name in names
                    for prefix in (
                        "src",
                        "backend.api",
                        "backend.auth",
                        "backend.analytics",
                    )
                ), path


def test_local_documentation_links_survive_the_moves():
    documents = [
        ROOT / "README.md",
        *(ROOT / "docs").rglob("*.md"),
        ROOT / "backend/README.md",
        ROOT / "frontend/README.md",
        ROOT / "ml/README.md",
        ROOT / "models/README.md",
        ROOT / "scripts/README.md",
    ]
    for path in documents:
        for destination in re.findall(
            r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")
        ):
            if destination.startswith(("http:", "https:", "#", "mailto:")):
                continue
            target = destination.split("#", 1)[0]
            assert (path.parent / target).exists(), (path.relative_to(ROOT), target)


def test_application_entrypoint_only_assembles_the_application():
    from backend.main import app, create_app

    tree = ast.parse((ROOT / "backend/main.py").read_text(encoding="utf-8"))
    functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert functions == ["create_app"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in {"get", "post", "put", "patch", "delete"}
    assert {
        (route.path, tuple(sorted(route.methods or [])))
        for route in create_app().routes
        if hasattr(route, "methods")
    } == {
        (route.path, tuple(sorted(route.methods or [])))
        for route in app.routes
        if hasattr(route, "methods")
    }


def test_module_services_do_not_depend_on_routers_or_the_entrypoint():
    for path in (ROOT / "backend/modules").rglob("service.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [item.name for item in node.names]
                if isinstance(node, ast.Import)
                else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            )
            for name in names:
                assert name != "backend.main" and not name.endswith(".router"), path
