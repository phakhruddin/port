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


def test_log_hygiene(deployment):
    # v2 addition: instruction.md required outcome #9 ("log request IDs and
    # authorization decisions without logging credentials, bearer tokens or
    # complete presigned URLs") had no automated check in v1. This inspects
    # the API task's captured CloudWatch log stream directly rather than
    # trusting a visual read of the requirement.
    logs = boto3.client("logs", region_name="us-east-1", endpoint_url="http://aws:4566")
    group = deployment["logs"]["api"]
    streams = logs.describe_log_streams(logGroupName=group)["logStreams"]
    assert streams, f"no log streams found in {group}"

    forbidden = {"bearer ", "authorization:", "x-amz-signature", "client_secret"}
    secrets = {
        deployment["auth"]["viewer_client_secret"],
        deployment["auth"]["contributor_a_client_secret"],
        deployment["auth"]["contributor_b_client_secret"],
        deployment["auth"]["admin_client_secret"],
    }

    checked_any = False
    for stream in streams:
        events = logs.get_log_events(logGroupName=group, logStreamName=stream["logStreamName"], limit=1000)["events"]
        for event in events:
            checked_any = True
            message = event["message"]
            lowered = message.lower()
            for pattern in forbidden:
                assert pattern not in lowered, f"log line contains forbidden pattern {pattern!r}: {message!r}"
            for secret in secrets:
                assert secret not in message, f"log line leaks a client secret: {message!r}"

    assert checked_any, f"no log events found in any stream under {group}"
