import json
import subprocess
from urllib.parse import urlparse

import requests

from .conftest import CONFIG, SUBMISSION


def test_required_layout():
    assert (SUBMISSION / "deploy.sh").is_file()
    assert (SUBMISSION / "destroy.sh").is_file()
    assert list((SUBMISSION / "infra").glob("*.tf"))


def test_terraform_configuration(deployment):
    result = subprocess.run(["terraform", f"-chdir={SUBMISSION / 'infra'}", "validate", "-no-color"], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_manifest_identity(deployment):
    config = json.loads(CONFIG.read_text())
    assert deployment["deployment"] == config["resource_prefix"]
    assert deployment["image"] == {"reference": config["api_image"], "id": config["api_image_id"]}
    assert deployment["compute"]["desired_count"] >= 2
    assert len(deployment["network"]["public_subnet_ids"]) >= 2
    assert len(deployment["network"]["private_subnet_ids"]) >= 2


def test_manifest_connectivity(deployment):
    # v2 addition: fails fast, with a specific diagnosis, on the single
    # highest-leverage defect found across every model run analyzed in
    # harbor-analysis/ — publishing the real (unresolvable-from-the-verifier)
    # ALB DNS name as alb.connect_url instead of the shared emulator
    # endpoint. Without this check, that mistake surfaces as three unrelated
    # RBAC/CRUD test failures instead of one clearly-labeled connectivity
    # defect. See contracts/architecture.md's "The manifest's alb object".
    connect_url = deployment["alb"]["connect_url"]
    dns_name = deployment["alb"].get("dns_name", "")
    parsed = urlparse(connect_url)
    assert parsed.scheme in ("http", "https") and parsed.hostname, (
        f"alb.connect_url {connect_url!r} is not a valid http(s) URL"
    )
    assert dns_name == "" or parsed.hostname != dns_name, (
        f"alb.connect_url uses the real ALB DNS name ({dns_name!r}). "
        "That hostname is not resolvable from the verifier's network "
        "namespace. Set alb.connect_url to the shared AWS-compatible "
        "endpoint instead (see contracts/architecture.md)."
    )
    try:
        response = requests.get(f"{connect_url}/health/live", timeout=10)
    except requests.RequestException as exc:
        raise AssertionError(
            f"alb.connect_url ({connect_url}) is not reachable from the verifier: {exc}. "
            "Confirm it points at the shared emulator endpoint, not the generated ALB DNS name."
        ) from exc
    assert response.status_code == 200, f"unexpected status from {connect_url}/health/live: {response.status_code}"
