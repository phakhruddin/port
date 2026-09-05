import json
import subprocess

import boto3

from .conftest import SUBMISSION


def test_endpoint_repair_preserves_storage(deployment):
    ec2 = boto3.client("ec2", region_name="us-east-1", endpoint_url="http://aws:4566")
    old_endpoint = deployment["network"]["s3_endpoint_id"]
    ec2.delete_vpc_endpoints(VpcEndpointIds=[old_endpoint])

    subprocess.run([str(SUBMISSION / "deploy.sh")], cwd=SUBMISSION, check=True, timeout=720)
    repaired = json.loads((SUBMISSION / "manifest.json").read_text())
    assert repaired["storage"] == deployment["storage"]
    endpoint = ec2.describe_vpc_endpoints(VpcEndpointIds=[repaired["network"]["s3_endpoint_id"]])["VpcEndpoints"][0]
    assert set(endpoint["RouteTableIds"]) == set(repaired["network"]["private_route_table_ids"])
