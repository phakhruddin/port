import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import requests

SOURCE_SUBMISSION = Path(os.getenv("SIGNEDGATE_SUBMISSION_DIR", "/workspace/submission"))
SUBMISSION = Path("/tmp/signedgate-submission")
CONFIG = Path(os.getenv("SIGNEDGATE_CONFIG", "/workspace/config/config.json"))
BACKUP_CONFIG = Path("/workspace/runtime-config/config.json")

# Harbor injects agent artifacts from a host-owned, read-only directory. The
# deployment contract requires Terraform state and generated files beside the
# submitted configuration, so exercise an exact writable copy instead.
shutil.copytree(SOURCE_SUBMISSION, SUBMISSION, dirs_exist_ok=True)


def pytest_sessionfinish(session, exitstatus):
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    passed = len(reporter.stats.get("passed", [])) if reporter else 0
    failed = len(reporter.stats.get("failed", [])) if reporter else 0
    errors = len(reporter.stats.get("error", [])) if reporter else 0
    total = passed + failed + errors
    score = round(100 * passed / total, 2) if total else 0
    output = Path("/logs/verifier/score.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"reward": score / 100, "score": score}) + "\n")


@pytest.fixture(scope="session")
def deployment():
    if not CONFIG.is_file() and BACKUP_CONFIG.is_file():
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BACKUP_CONFIG, CONFIG)
    assert CONFIG.is_file(), f"runtime configuration is missing at {CONFIG}"
    deploy = SUBMISSION / "deploy.sh"
    assert deploy.is_file(), "deploy.sh is missing"
    assert os.access(deploy, os.X_OK), "deploy.sh must be executable"
    subprocess.run([str(deploy)], cwd=SUBMISSION, check=True, timeout=720)
    manifest = json.loads((SUBMISSION / "manifest.json").read_text())
    return manifest


def token(manifest, role):
    client_id = manifest["auth"][f"{role}_client_id"]
    secret = manifest["auth"][f"{role}_client_secret"]
    scope = "contributor" if role.startswith("contributor_") else role
    response = requests.post(
        manifest["auth"]["token_url"],
        auth=(client_id, secret),
        data={"grant_type": "client_credentials", "scope": f"signedgate/{scope}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def credentials(deployment):
    return {role: token(deployment, role) for role in ["viewer", "contributor_a", "contributor_b", "admin"]}
