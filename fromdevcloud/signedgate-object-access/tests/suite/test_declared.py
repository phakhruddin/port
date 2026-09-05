import json
import os
import subprocess
from pathlib import Path

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
