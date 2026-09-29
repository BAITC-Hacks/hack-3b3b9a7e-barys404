"""Receive code releases through the dedicated, restricted deployment SSH key."""

import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path, PurePosixPath


APPS = Path("/home/barys404/apps")
BASE = APPS / "medflow-deploy"
ORIGINAL = APPS / "medflow-5ae817c"
CURRENT = APPS / "medflow-current"
PYTHON = Path("/home/barys404/.local/bin/python3.12")
REQUIREMENTS = ("requirements-api.txt", "backend/requirements.txt", "ml/requirements.txt")
SHARED = (".env", "data", "models", ".runtime")
ROOTS = {"backend", "frontend", "ml", "scripts", "docs"}
SERVICE = "medflow.service"
MAX_ARCHIVE = 40 * 1024**2
MAX_CONTENT = 150 * 1024**2
PRECHECK = """
from backend.main import app
from backend.http.data import require_ready
from ml.predict import load_model, model_status
from ml.load_forecast import forecast_status
report = require_ready()
assert model_status()['available'], 'Waiting model is unavailable'
assert forecast_status(report)['available'], 'Flow model is unavailable'
load_model()
print('Application, current dataset and both models verified.', flush=True)
"""


def run(*args, cwd=None, timeout=120):
    environment = os.environ.copy()
    environment.update(
        MEDFLOW_ENV="production",
        MEDFLOW_ORIGINS="https://barys404.govtech-kz.com",
        MEDFLOW_MEMORY_LIMIT="256MB",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        PYTHONUNBUFFERED="1",
    )
    subprocess.run(args, cwd=cwd, env=environment, check=True, timeout=timeout)


def dependency_id(release):
    digest = hashlib.sha256(b"medflow-python-3.12\0")
    for name in REQUIREMENTS:
        digest.update(name.encode() + b"\0" + (release / name).read_bytes())
    return digest.hexdigest()


def switch_to(release):
    with tempfile.TemporaryDirectory(prefix=".medflow-current-", dir=APPS) as directory:
        temporary = Path(directory) / "current"
        temporary.symlink_to(release, target_is_directory=True)
        os.replace(temporary, CURRENT)


def save_state(current, previous):
    payload = json.dumps({"current": str(current), "previous": str(previous)})
    with tempfile.NamedTemporaryFile(mode="w", dir=BASE, delete=False) as output:
        output.write(payload)
        temporary = Path(output.name)
    os.replace(temporary, BASE / "state.json")


def initialize():
    if CURRENT.exists() or CURRENT.is_symlink():
        raise ValueError("Current release link already exists; initialization cancelled")
    for name in (*SHARED, ".venv", *REQUIREMENTS):
        if not (ORIGINAL / name).exists():
            raise ValueError(f"Original deployment is missing {name}")
    for name in ("releases", "environments", "incoming", "failed"):
        (BASE / name).mkdir(mode=0o700, parents=True, exist_ok=True)
    environment = BASE / "environments" / dependency_id(ORIGINAL)
    environment.symlink_to(ORIGINAL / ".venv", target_is_directory=True)
    switch_to(ORIGINAL)
    save_state(ORIGINAL, ORIGINAL)
    print("Original deployment registered as the rollback baseline.", flush=True)


def receive_archive(expected_hash):
    with tempfile.NamedTemporaryFile(dir=BASE / "incoming", suffix=".tar.gz", delete=False) as output:
        path = Path(output.name)
        digest = hashlib.sha256()
        total = 0
        while chunk := sys.stdin.buffer.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_ARCHIVE:
                path.unlink(missing_ok=True)
                raise ValueError("Deployment archive exceeds 40MB")
            digest.update(chunk)
            output.write(chunk)
    if digest.hexdigest() != expected_hash:
        path.unlink(missing_ok=True)
        raise ValueError("Deployment archive checksum mismatch")
    return path


def unpack(archive_path, release):
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        if len(members) > 5000 or sum(item.size for item in members) > MAX_CONTENT:
            raise ValueError("Deployment archive contains too many or too large files")
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError("Invalid deployment archive path")
            if path.parts[0] not in ROOTS and str(path) not in {"README.md", "requirements-api.txt"}:
                raise ValueError("Deployment archive contains non-code files")
            if any(part in {".git", ".venv", ".runtime", "node_modules"} or part.startswith(".env") for part in path.parts):
                raise ValueError("Deployment archive contains local or secret files")
            if not member.isdir() and not member.isfile():
                raise ValueError("Links and special files are not permitted")
        release.mkdir(mode=0o700)
        archive.extractall(release, members=members, filter="data")
    required = ("backend/main.py", "frontend/dist/index.html", *REQUIREMENTS)
    for name in required:
        if not (release / name).is_file():
            raise ValueError(f"Deployment archive is missing {name}")
    for name in SHARED:
        (release / name).symlink_to(ORIGINAL / name, target_is_directory=name != ".env")


def prepare_environment(release):
    environment = BASE / "environments" / dependency_id(release)
    if environment.exists() and not environment.is_symlink() and not (environment / ".deployment-ready").exists():
        archived = BASE / "failed" / f"environment-{environment.name}-{time.time_ns()}"
        environment.rename(archived)
    if not environment.exists():
        if shutil.disk_usage(BASE).free < 2500 * 1024**2:
            raise ValueError("At least 2.5GB free space is required to install changed dependencies")
        run(str(PYTHON), "-m", "venv", str(environment))
        run(
            str(environment / "bin/python"), "-m", "pip", "install",
            "--no-cache-dir", "--only-binary=:all:", "-r", "requirements-api.txt",
            cwd=release, timeout=600,
        )
        (environment / ".deployment-ready").touch(mode=0o600)
    (release / ".venv").symlink_to(environment, target_is_directory=True)


def wait_for_site(release):
    expected = (release / "frontend/dist/index.html").read_bytes()
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen("http://127.0.0.1:8010/api/health", timeout=2) as response:
                healthy = json.load(response).get("status") == "ok"
            with urllib.request.urlopen("http://127.0.0.1:8010/", timeout=2) as response:
                current_index = response.read()
            if healthy and current_index == expected:
                return
        except (OSError, ValueError):
            pass
        time.sleep(1)
    raise RuntimeError("Application did not become healthy within 90 seconds")


def activate(release):
    previous = CURRENT.resolve(strict=True)
    switch_to(release)
    try:
        run("systemctl", "--user", "restart", SERVICE)
        wait_for_site(release)
        save_state(release, previous)
    except Exception:
        switch_to(previous)
        run("systemctl", "--user", "restart", SERVICE)
        wait_for_site(previous)
        print("Deployment failed; previous release restored.", flush=True)
        raise
    print(f"Deployment active: {release.name}", flush=True)


def deploy(commit, checksum):
    archive = receive_archive(checksum)
    release = BASE / "releases" / f"{commit}-{checksum[:16]}"
    try:
        if release.exists() and not (release / ".deployment.json").exists():
            release.rename(BASE / "failed" / f"release-{release.name}-{time.time_ns()}")
        if release.exists():
            receipt = json.loads((release / ".deployment.json").read_text())
            if receipt["archive_sha256"] != checksum:
                raise ValueError("This commit already has a different deployment archive")
        else:
            unpack(archive, release)
            prepare_environment(release)
            (release / ".deployment.json").write_text(json.dumps({"archive_sha256": checksum}))
        print("Verifying code and existing models before switching the site...", flush=True)
        run(str(release / ".venv/bin/python"), "-c", PRECHECK, cwd=release, timeout=180)
        activate(release)
    finally:
        archive.unlink(missing_ok=True)


def rollback():
    state = json.loads((BASE / "state.json").read_text())
    previous = Path(state["previous"]).resolve(strict=True)
    if previous != ORIGINAL and previous.parent != (BASE / "releases"):
        raise ValueError("Rollback target is outside the deployment directories")
    activate(previous)


def main():
    os.umask(0o077)
    BASE.mkdir(mode=0o700, exist_ok=True)
    with (BASE / "deploy.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if len(sys.argv) == 2 and sys.argv[1] == "--initialize":
            initialize()
            return
        if len(sys.argv) == 2 and sys.argv[1] == "--rollback":
            rollback()
            return
        match = re.fullmatch(r"deploy ([0-9a-f]{40}) ([0-9a-f]{64})", os.environ.get("SSH_ORIGINAL_COMMAND", ""))
        if not match or len(sys.argv) != 1:
            raise ValueError("Only the deployment command is permitted for this SSH key")
        deploy(*match.groups())


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, tarfile.TarError, KeyError) as error:
        print(f"Deployment failed: {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)
