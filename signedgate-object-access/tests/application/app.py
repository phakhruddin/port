import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

import boto3
import jwt
import requests
from boto3.dynamodb.conditions import Attr
from botocore.config import Config
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("signedgate")
app = FastAPI(title="SignedGate")

REGION = os.environ["AWS_REGION"]
ENDPOINT = os.environ["AWS_ENDPOINT_URL"].rstrip("/")
BUCKET = os.environ["OBJECT_BUCKET"]
TABLE_NAME = os.environ["METADATA_TABLE"]
TTL = min(int(os.getenv("PRESIGN_TTL_SECONDS", "120")), 300)
ISSUER = os.environ["COGNITO_ISSUER"]
JWKS_URL = os.environ["COGNITO_JWKS_URL"]
AUDIENCES = set(os.environ["COGNITO_AUDIENCES"].split(","))

session = boto3.session.Session(region_name=REGION)
s3 = session.client("s3", endpoint_url=ENDPOINT, config=Config(s3={"addressing_style": "path"}, signature_version="s3v4"))
ddb = session.resource("dynamodb", endpoint_url=ENDPOINT).Table(TABLE_NAME)
_jwks = {"value": None, "expires": 0.0}


class CreateFile(BaseModel):
    filename: str = Field(min_length=1, max_length=180)
    content_type: str = Field(default="application/octet-stream", max_length=120)


class ShareFile(BaseModel):
    subject: str = Field(min_length=1, max_length=200)


def safe_filename(value: str) -> str:
    leaf = value.replace("\\", "/").split("/")[-1]
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", leaf).strip(".")
    if not cleaned or cleaned in {".", ".."}:
        raise HTTPException(400, "invalid filename")
    return cleaned[:180]


def jwks():
    if _jwks["value"] is None or time.time() >= _jwks["expires"]:
        response = requests.get(JWKS_URL, timeout=3)
        response.raise_for_status()
        _jwks["value"] = response.json()
        _jwks["expires"] = time.time() + 300
    return _jwks["value"]


def identity(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "bearer token required")
    token = authorization[7:]
    try:
        header = jwt.get_unverified_header(token)
        key_data = next(k for k in jwks()["keys"] if k["kid"] == header["kid"])
        key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
        claims = jwt.decode(token, key, algorithms=["RS256"], issuer=ISSUER, options={"verify_aud": False})
    except Exception as exc:
        raise HTTPException(401, "invalid token") from exc
    audience = claims.get("client_id") or claims.get("aud")
    if audience not in AUDIENCES:
        raise HTTPException(401, "invalid audience")
    scopes = set(str(claims.get("scope", "")).split())
    roles = {s.rsplit("/", 1)[-1] for s in scopes if s.startswith("signedgate/")}
    if not roles:
        raise HTTPException(403, "role scope required")
    return {"subject": claims.get("sub") or audience, "roles": roles}


def authorize(item, who, operation):
    roles = who["roles"]
    owner = item["owner_sub"] == who["subject"]
    shared = who["subject"] in item.get("shared_with", [])
    allowed = "admin" in roles or (operation == "read" and shared) or (owner and "contributor" in roles)
    if not allowed:
        raise HTTPException(403, "operation denied")


def record(file_id: str):
    item = ddb.get_item(Key={"file_id": file_id}, ConsistentRead=True).get("Item")
    if not item:
        raise HTTPException(404, "file not found")
    return item


def signed(operation, item, content_type=None):
    params = {"Bucket": BUCKET, "Key": item["object_key"]}
    if content_type:
        params["ContentType"] = content_type
    return {"method": {"get_object": "GET", "put_object": "PUT", "delete_object": "DELETE"}[operation],
            "url": s3.generate_presigned_url(operation, Params=params, ExpiresIn=TTL), "expires_in": TTL}


@app.middleware("http")
async def request_log(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    response = await call_next(request)
    log.info("request_id=%s method=%s path=%s status=%s", request_id, request.method, request.url.path, response.status_code)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health/live")
def live():
    return {"status": "UP"}


@app.get("/health/ready")
def ready():
    try:
        s3.head_bucket(Bucket=BUCKET)
        ddb.load()
        return {"status": "UP"}
    except Exception as exc:
        raise HTTPException(503, "storage unavailable") from exc


@app.post("/v1/files", status_code=201)
def create(body: CreateFile, who=Depends(identity)):
    if not ({"contributor", "admin"} & who["roles"]):
        raise HTTPException(403, "create denied")
    file_id = str(uuid.uuid4())
    filename = safe_filename(body.filename)
    item = {"file_id": file_id, "object_key": f"tenants/{quote(who['subject'], safe='')}/{file_id}/{filename}",
            "owner_sub": who["subject"], "filename": filename, "content_type": body.content_type,
            "shared_with": [], "created_at": datetime.now(timezone.utc).isoformat()}
    ddb.put_item(Item=item, ConditionExpression="attribute_not_exists(file_id)")
    return {"file": item, "upload": signed("put_object", item, body.content_type)}


@app.get("/v1/files")
def list_files(who=Depends(identity)):
    items = ddb.scan().get("Items", [])
    if "admin" not in who["roles"]:
        items = [i for i in items if i["owner_sub"] == who["subject"] or who["subject"] in i.get("shared_with", [])]
    return {"files": items}


@app.get("/v1/files/{file_id}")
def get_file(file_id: str, who=Depends(identity)):
    item = record(file_id); authorize(item, who, "read")
    return item


@app.post("/v1/files/{file_id}/download-url")
def download(file_id: str, who=Depends(identity)):
    item = record(file_id); authorize(item, who, "read")
    return signed("get_object", item)


@app.post("/v1/files/{file_id}/update-url")
def update(file_id: str, who=Depends(identity)):
    item = record(file_id); authorize(item, who, "update")
    return signed("put_object", item, item.get("content_type"))


@app.delete("/v1/files/{file_id}")
def delete(file_id: str, who=Depends(identity)):
    item = record(file_id); authorize(item, who, "delete")
    return signed("delete_object", item)


@app.post("/v1/files/{file_id}/shares")
def share(file_id: str, body: ShareFile, who=Depends(identity)):
    item = record(file_id); authorize(item, who, "update")
    shared = sorted(set(item.get("shared_with", [])) | {body.subject})
    ddb.update_item(Key={"file_id": file_id}, UpdateExpression="SET shared_with = :s", ExpressionAttributeValues={":s": shared})
    return {"file_id": file_id, "shared_with": shared}
