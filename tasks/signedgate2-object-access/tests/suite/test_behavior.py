import uuid

import requests


def call(base, method, path, token, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{base}{path}", headers=headers, timeout=10, **kwargs)


def create_file(base, token, filename="proof.txt", content=b"signedgate-proof", content_type="text/plain"):
    created = call(base, "POST", "/v1/files", token, json={"filename": filename, "content_type": content_type})
    assert created.status_code == 201, created.text
    payload = created.json()
    put = requests.put(payload["upload"]["url"], data=content, headers={"content-type": content_type}, timeout=10)
    assert put.status_code < 300, put.text
    return payload["file"]["file_id"], payload


def test_contributor_can_create_and_upload(deployment, credentials):
    base = deployment["alb"]["connect_url"]
    created = call(base, "POST", "/v1/files", credentials["contributor_a"], json={"filename": "proof.txt", "content_type": "text/plain"})
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["upload"]["method"] == "PUT"
    assert 0 < payload["upload"]["expires_in"] <= 300
    assert requests.put(payload["upload"]["url"], data=b"signedgate-proof", headers={"content-type": "text/plain"}, timeout=10).status_code < 300


def test_owner_can_download_and_delete(deployment, credentials):
    base = deployment["alb"]["connect_url"]
    file_id, _ = create_file(base, credentials["contributor_a"])

    download = call(base, "POST", f"/v1/files/{file_id}/download-url", credentials["contributor_a"])
    assert download.status_code == 200
    assert requests.get(download.json()["url"], timeout=10).content == b"signedgate-proof"

    deletion = call(base, "DELETE", f"/v1/files/{file_id}", credentials["contributor_a"])
    assert deletion.status_code == 200
    assert requests.delete(deletion.json()["url"], timeout=10).status_code < 300


def test_cross_tenant_read_denied(deployment, credentials):
    base = deployment["alb"]["connect_url"]
    file_id, _ = create_file(base, credentials["contributor_a"], filename=f"{uuid.uuid4()}.txt")
    denied = call(base, "POST", f"/v1/files/{file_id}/download-url", credentials["contributor_b"])
    assert denied.status_code == 403


def test_admin_can_access_any_file(deployment, credentials):
    base = deployment["alb"]["connect_url"]
    file_id, _ = create_file(base, credentials["contributor_a"], filename=f"{uuid.uuid4()}.txt")
    as_admin = call(base, "POST", f"/v1/files/{file_id}/download-url", credentials["admin"])
    assert as_admin.status_code == 200


def test_viewer_cannot_create(deployment, credentials):
    response = call(deployment["alb"]["connect_url"], "POST", "/v1/files", credentials["viewer"], json={"filename": "blocked.txt"})
    assert response.status_code == 403


def test_key_confinement(deployment, credentials):
    response = call(deployment["alb"]["connect_url"], "POST", "/v1/files", credentials["contributor_a"], json={"filename": "../../escape.txt"})
    assert response.status_code == 201
    key = response.json()["file"]["object_key"]
    assert key.startswith("tenants/") and ".." not in key and key.endswith("/escape.txt")
