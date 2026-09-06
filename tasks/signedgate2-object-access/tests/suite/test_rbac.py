"""Closes test-coverage gaps identified in harbor-analysis/: instruction.md
required outcome #6 (a viewer must be able to read a file genuinely shared
with them, not merely be denied creation) and #7 (unsigned requests and
altered signatures must be rejected) were stated requirements with no
corresponding v1 test.
"""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from .test_behavior import call, create_file


def test_viewer_can_read_shared_file(deployment, credentials):
    base = deployment["alb"]["connect_url"]
    file_id, _ = create_file(base, credentials["contributor_a"])

    viewer_subject = deployment["auth"]["viewer_client_id"]
    shared = call(base, "POST", f"/v1/files/{file_id}/shares", credentials["contributor_a"], json={"subject": viewer_subject})
    assert shared.status_code == 200, shared.text

    download = call(base, "POST", f"/v1/files/{file_id}/download-url", credentials["viewer"])
    assert download.status_code == 200, download.text
    assert requests.get(download.json()["url"], timeout=10).content == b"signedgate-proof"


def test_unsigned_request_rejected(deployment, credentials):
    base = deployment["alb"]["connect_url"]
    file_id, _ = create_file(base, credentials["contributor_a"])
    download = call(base, "POST", f"/v1/files/{file_id}/download-url", credentials["contributor_a"])
    assert download.status_code == 200
    signed_url = download.json()["url"]

    unsigned = urlunparse(urlparse(signed_url)._replace(query=""))
    response = requests.get(unsigned, timeout=10)
    assert response.status_code in (401, 403), (
        f"expected an unsigned request to be rejected, got {response.status_code}"
    )


def test_signature_tamper_rejected(deployment, credentials):
    base = deployment["alb"]["connect_url"]
    file_id, _ = create_file(base, credentials["contributor_a"])
    download = call(base, "POST", f"/v1/files/{file_id}/download-url", credentials["contributor_a"])
    assert download.status_code == 200
    signed_url = download.json()["url"]

    parsed = urlparse(signed_url)
    params = dict(parse_qsl(parsed.query))
    signature_key = next((k for k in params if k.lower().endswith("signature")), None)
    assert signature_key, f"presigned URL has no signature parameter to tamper with: {signed_url}"
    original = params[signature_key]
    params[signature_key] = ("0" if original[:1] != "0" else "1") + original[1:]
    tampered = urlunparse(parsed._replace(query=urlencode(params)))

    response = requests.get(tampered, timeout=10)
    assert response.status_code in (401, 403), (
        f"expected a tampered signature to be rejected, got {response.status_code}"
    )
