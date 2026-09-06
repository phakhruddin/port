import os
import subprocess

from .conftest import SUBMISSION


def test_stable_redeployment(deployment):
    # Floci omits/defaults several read-back fields and does not implement
    # ModifyVpcEndpoint, which creates false provider drift on refresh. Verify
    # that the submitted configuration and recorded state are intrinsically
    # stable; the recovery test separately exercises a real redeployment.
    plan_env = os.environ.copy()
    plan_env["TF_VAR_aws_access_key_id"] = os.environ["AWS_ACCESS_KEY_ID"]
    plan_env["TF_VAR_aws_secret_access_key"] = os.environ["AWS_SECRET_ACCESS_KEY"]
    plan = subprocess.run(
        ["terraform", f"-chdir={SUBMISSION / 'infra'}", "plan", "-input=false", "-refresh=false", "-detailed-exitcode", "-no-color"],
        text=True,
        capture_output=True,
        timeout=300,
        env=plan_env,
    )
    if plan.returncode not in (0, 2):
        raise AssertionError(
            "standalone `terraform plan` against infra/ failed outright "
            "(not just 'changes proposed'). This usually means a required "
            "variable is only ever supplied via a -var flag inside "
            "deploy.sh rather than persisted to an auto-loaded variable "
            "file (e.g. infra/config.auto.tfvars.json) — see "
            "contracts/architecture.md's \"Shared rules\". "
            f"terraform output:\n{plan.stdout}{plan.stderr}"
        )
    plan_text = plan.stdout.lower()
    assert 'aws_s3_bucket.objects must be replaced' not in plan_text
    assert 'aws_dynamodb_table.metadata must be replaced' not in plan_text
    if plan.returncode == 2:
        assert deployment["storage"]["bucket"] in plan.stdout
        assert deployment["storage"]["metadata_table"] in plan.stdout
