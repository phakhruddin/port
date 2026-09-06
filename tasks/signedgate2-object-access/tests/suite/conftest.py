import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import requests
import yaml

SOURCE_SUBMISSION = Path(os.getenv("SIGNEDGATE_SUBMISSION_DIR", "/workspace/submission"))
SUBMISSION = Path("/tmp/signedgate-submission")
CONFIG = Path(os.getenv("SIGNEDGATE_CONFIG", "/workspace/config/config.json"))
BACKUP_CONFIG = Path("/workspace/runtime-config/config.json")
OBLIGATIONS = yaml.safe_load((Path(__file__).parent / "obligations.yaml").read_text())["categories"]

# Harbor injects agent artifacts from a host-owned, read-only directory. The
# deployment contract requires Terraform state and generated files beside the
# submitted configuration, so exercise an exact writable copy instead.
shutil.copytree(SOURCE_SUBMISSION, SUBMISSION, dirs_exist_ok=True)

# v2 scoring: every collected test maps to exactly one category from
# obligations.yaml. This table is the single source of truth for that
# mapping — keep it in sync with reasoning.md's "Test-to-category mapping"
# table in the task package, which documents *why* each test lives where it
# does. Unlike v1, the final score is computed per category and weighted by
# these categories' points, not as one flat ratio over every pytest result —
# see pytest_sessionfinish below.
CATEGORY_BY_TEST = {
    # networking_and_traffic
    "test_required_layout": "networking_and_traffic",
    "test_manifest_identity": "networking_and_traffic",
    "test_manifest_connectivity": "networking_and_traffic",
    "test_private_network_graph": "networking_and_traffic",
    # recovery_and_redeployment
    "test_terraform_configuration": "recovery_and_redeployment",
    "test_stable_redeployment": "recovery_and_redeployment",
    "test_endpoint_repair_preserves_storage": "recovery_and_redeployment",
    # presigned_crud
    "test_contributor_can_create_and_upload": "presigned_crud",
    "test_owner_can_download_and_delete": "presigned_crud",
    "test_key_confinement": "presigned_crud",
    # rbac_and_isolation
    "test_viewer_cannot_create": "rbac_and_isolation",
    "test_cross_tenant_read_denied": "rbac_and_isolation",
    "test_admin_can_access_any_file": "rbac_and_isolation",
    "test_viewer_can_read_shared_file": "rbac_and_isolation",
    # security_and_encryption
    "test_storage_security": "security_and_encryption",
    "test_unsigned_request_rejected": "security_and_encryption",
    "test_signature_tamper_rejected": "security_and_encryption",
    # observability_and_cleanup
    "test_log_hygiene": "observability_and_cleanup",
    "test_clean_destroy": "observability_and_cleanup",
}


def pytest_sessionfinish(session, exitstatus):
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    stats = reporter.stats if reporter else {}

    tally = {category: {"passed": 0, "total": 0} for category in OBLIGATIONS}
    unmapped = []
    for outcome in ("passed", "failed", "error"):
        for report in stats.get(outcome, []):
            name = report.nodeid.split("::")[-1].split("[")[0]
            category = CATEGORY_BY_TEST.get(name)
            if category is None:
                unmapped.append(name)
                continue
            tally[category]["total"] += 1
            if outcome == "passed":
                tally[category]["passed"] += 1

    categories = {}
    score = 0.0
    for category, weight in OBLIGATIONS.items():
        passed = tally[category]["passed"]
        total = tally[category]["total"]
        ratio = (passed / total) if total else 0.0
        earned = round(weight * ratio, 4)
        score += earned
        categories[category] = {"weight": weight, "passed": passed, "total": total, "earned": round(earned, 2)}

    score = round(score, 2)
    output = Path("/logs/verifier/score.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "reward": round(score / 100, 4),
                "score": score,
                "categories": categories,
                "unmapped_tests": sorted(set(unmapped)),
            },
            indent=2,
        )
        + "\n"
    )


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
