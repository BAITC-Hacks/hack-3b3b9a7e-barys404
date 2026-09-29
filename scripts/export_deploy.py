import argparse
import io
import json
import os
import tarfile
import tempfile
from pathlib import Path

from backend.core.config import DATA_DIR, MODELS_DIR, PROCESSED_DIR, ROOT
from backend.data_pipeline.data_loader import discover_files, fingerprint_policy, source_fingerprint
from backend.data_pipeline.deployment import (
    ARTIFACT_NAMES,
    MANIFEST_NAME,
    artifact_path,
    file_record,
    file_version,
    source_records,
)

RUNTIME_CODE = (
    "backend/data_pipeline/data_loader.py",
    "backend/data_pipeline/deployment.py",
    "backend/http/data.py",
    "ml/predict.py",
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_current_artifacts(fingerprint: str) -> None:
    report = _read_json(PROCESSED_DIR / "data_quality_report.json")
    if not report.get("pipeline_complete") or report.get("source_fingerprint") != fingerprint:
        raise ValueError("Prepared data is incomplete or stale. Export cancelled.")
    for name in ("model_metadata.json", "referral_load_7day_metadata.json", "temporal_validation.json"):
        if _read_json(MODELS_DIR / name).get("source_fingerprint") != fingerprint:
            raise ValueError(f"{name} belongs to another dataset. Export cancelled.")


def _archive_files(files: dict, include_runtime_code: bool) -> dict[str, Path]:
    paths = {
        name: artifact_path(name, PROCESSED_DIR, MODELS_DIR)
        for name in ARTIFACT_NAMES
    }
    for sources in files.values():
        for path in sources:
            relative = path.relative_to(DATA_DIR)
            paths[(Path("data") / relative).as_posix()] = path
    if include_runtime_code:
        paths.update({name: ROOT / name for name in RUNTIME_CODE})
    for path in paths.values():
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Expected a regular file: {path.name}")
    return paths


def _build_manifest(files: dict, fingerprint: str) -> dict:
    manifest = {
        "version": 1,
        "policy": fingerprint_policy(),
        "source_fingerprint": fingerprint,
        "sources": source_records(files),
        "artifacts": {
            name: file_record(artifact_path(name, PROCESSED_DIR, MODELS_DIR))
            for name in ARTIFACT_NAMES
        },
    }
    metadata = _read_json(MODELS_DIR / "referral_load_7day_metadata.json")
    if (
        metadata.get("hospital_day_sha256")
        != manifest["artifacts"]["data/processed/hospital_day.parquet"]["sha256"]
        or metadata.get("model_sha256")
        != manifest["artifacts"]["models/referral_load_7day_catboost.cbm"]["sha256"]
    ):
        raise ValueError("Forecast artifacts changed. Export cancelled.")
    return manifest


def _owner_only(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.mode &= 0o700
    return info


def _write_archive(
    output: Path, paths: dict[str, Path], manifest: dict, versions: dict[str, tuple], files: dict
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".partial", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with tarfile.open(temporary_path, "w:gz", compresslevel=3) as archive:
            for name, path in paths.items():
                archive.add(path, arcname=name, recursive=False, filter=_owner_only)
            payload = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
            info = tarfile.TarInfo(f"data/processed/{MANIFEST_NAME}")
            info.size = len(payload)
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(payload))
        if any(file_version(paths[name]) != version for name, version in versions.items()):
            raise ValueError("Files changed during export. Retry with a stable dataset.")
        if discover_files() != files:
            raise ValueError("Source file list changed during export.")
        _require_current_artifacts(source_fingerprint(files))
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)


def export_deploy(output: Path, include_runtime_code: bool = False) -> None:
    if output.exists():
        raise ValueError("Output already exists. Choose another archive name.")
    files = discover_files()
    if not all(files.values()):
        raise ValueError("All four source categories are required for this export.")
    fingerprint = source_fingerprint(files)
    _require_current_artifacts(fingerprint)
    paths = _archive_files(files, include_runtime_code)
    versions = {name: file_version(path) for name, path in paths.items()}
    print("Hashing CSV, prepared data and models...", flush=True)
    manifest = _build_manifest(files, fingerprint)
    if any(file_version(paths[name]) != version for name, version in versions.items()):
        raise ValueError("Files changed during verification. Export cancelled.")
    print("Creating deployment archive...", flush=True)
    _write_archive(output, paths, manifest, versions, files)
    print(f"Archive ready: {output}", flush=True)
    print(f"Size: {output.stat().st_size / 1024 ** 2:.1f} MiB. CSV files: {sum(map(len, files.values()))}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export existing data and models without training.")
    parser.add_argument("--output", type=Path, default=ROOT / ".runtime/deploy/data-models-portable.tar.gz")
    parser.add_argument("--include-runtime-code", action="store_true")
    args = parser.parse_args()
    try:
        export_deploy(args.output.resolve(), args.include_runtime_code)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(1, f"Export failed: {exc}\n")


if __name__ == "__main__":
    main()
