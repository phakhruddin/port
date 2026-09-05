# Runtime Contract

## Supplied image

| Component | Image tag | Entrypoint |
|---|---|---|
| SignedGate API | `signedgate/api:1.0.0` | `/app/start.sh` |

The exact `api_image` reference and `api_image_id` are supplied in
`/workspace/config/config.json`. Do not create ECR or rebuild the application.

## Configuration file

The generated JSON object contains:

| Field | Use |
|---|---|
| `resource_prefix` | Resource names and deployment tag |
| `region` | AWS provider and runtime region |
| `aws_endpoint_url` | AWS-compatible API endpoint |
| `api_image` | ECS container image |
| `api_image_id` | Immutable image identity for the manifest |
| `presign_ttl_seconds` | Required URL lifetime; never exceed 300 |

## API environment

Set these variables on the sole ECS container:

- `AWS_ENDPOINT_URL`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `OBJECT_BUCKET`
- `METADATA_TABLE`
- `PRESIGN_TTL_SECONDS`
- `COGNITO_ISSUER`
- `COGNITO_JWKS_URL`
- `COGNITO_AUDIENCES` as comma-separated client IDs
- `BIND_ADDR=0.0.0.0:8080`

The endpoint hostname visible to the client is the hostname portion of
`aws_endpoint_url`. Presigned URLs must use that reachable endpoint and S3
path-style addressing.

`/health/live` reports process health. `/health/ready` succeeds only when S3
and DynamoDB are reachable. Logs must not contain tokens, credentials, client
secrets, signatures or complete presigned URLs.

## Deployment lifecycle

`deploy.sh` may run more than once. It must preserve the bucket, objects,
metadata table and records, while repairing drift in managed resources. A
post-deployment detailed plan may contain harmless provider readback updates,
but no creates, deletes or replacements.
