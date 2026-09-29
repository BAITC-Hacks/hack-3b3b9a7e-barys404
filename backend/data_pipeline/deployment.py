import hashlib
import json
from functools import lru_cache
from pathlib import Path
from threading import RLock

MANIFEST_NAME = "deployment_manifest.json"
ARTIFACT_NAMES = (
    "data/processed/analytical.parquet",
    "data/processed/waiting.parquet",
    "data/processed/refusals.parquet",
    "data/processed/treated.parquet",
    "data/processed/hospital_day.parquet",
    "data/processed/refusal_day.parquet",
    "data/processed/referral_key_quarantine.parquet",
    "data/processed/aggregation_summary.json",
    "data/processed/data_quality_report.json",
    "models/waiting_time_catboost.cbm",
    "models/model_metadata.json",
    "models/referral_load_7day_catboost.cbm",
    "models/referral_load_7day_metadata.json",
    "models/referral_load_7day_catboost.validation.parquet",
    "models/temporal_validation.json",
)
_hash_lock = RLock()


class DeploymentDataError(ValueError):
    pass


def file_version(path: Path) -> tuple:
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def file_sha256(path: Path) -> str:
    with _hash_lock:
        version = file_version(path)
        digest = _file_sha256(str(path.resolve()), version)
        if file_version(path) != version:
            raise DeploymentDataError("File changed during verification.")
        return digest


@lru_cache(maxsize=128)
def _file_sha256(path: str, version: tuple) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path) -> dict:
    version = file_version(path)
    digest = file_sha256(path)
    if file_version(path) != version:
        raise DeploymentDataError("File changed during verification.")
    return {"size": version[2], "sha256": digest}


def source_records(files: dict) -> list[dict]:
    records = [
        {"category": category, "name": path.name, **file_record(path)}
        for category, paths in files.items()
        for path in paths
    ]
    return sorted(records, key=lambda row: (row["category"], row["name"], row["sha256"]))


def artifact_path(name: str, processed_dir: Path, models_dir: Path) -> Path:
    if name not in ARTIFACT_NAMES:
        raise DeploymentDataError("Unexpected deployment artifact.")
    directory = processed_dir if name.startswith("data/processed/") else models_dir
    return directory / Path(name).name


def deployment_fingerprint(
    files: dict, policy: dict, processed_dir: Path, models_dir: Path
) -> str | None:
    path = processed_dir / MANIFEST_NAME
    if not path.exists():
        return None

    try:
        with _hash_lock:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            return _verify_manifest(manifest, files, policy, processed_dir, models_dir)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise DeploymentDataError(
            "Набор для деплоя изменился или неполон. Восстановите его из архива."
        ) from exc


def _verify_manifest(
    manifest: dict, files: dict, policy: dict, processed_dir: Path, models_dir: Path
) -> str:
    if manifest["version"] != 1 or manifest["policy"] != policy:
        raise DeploymentDataError("Deployment policy changed.")

    fingerprint = manifest["source_fingerprint"]
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise DeploymentDataError("Invalid source fingerprint.")
    int(fingerprint, 16)

    if source_records(files) != manifest["sources"]:
        raise DeploymentDataError("Source CSV changed.")

    artifacts = manifest["artifacts"]
    if set(artifacts) != set(ARTIFACT_NAMES):
        raise DeploymentDataError("Deployment artifacts are incomplete.")
    for name in ARTIFACT_NAMES:
        if file_record(artifact_path(name, processed_dir, models_dir)) != artifacts[name]:
            raise DeploymentDataError("Prepared data or model changed.")
    return fingerprint
