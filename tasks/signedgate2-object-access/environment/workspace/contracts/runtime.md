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
secrets, signatures or complete presigned URLs — this is verified directly
by `tests/suite/test_recovery.py::test_log_hygiene`, which inspects the
captured API log stream for these patterns rather than trusting a visual
read of `instruction.md`.

## Deployment lifecycle

`deploy.sh` may run more than once. It must preserve the bucket, objects,
metadata table and records, while repairing drift in managed resources. A
post-deployment detailed plan (`terraform plan -refresh=false`, run
standalone against `infra/`) must contain **no** proposed creates, updates,
or deletes — not merely no destructive replacements. See
`architecture.md`'s note on persisting Terraform inputs to an auto-loaded
variable file; this is what makes that standalone plan possible at all.

## Environment parity guarantee

The verifier's container image (`tests/runtime/Dockerfile`) installs the
same tool set as this environment's image: `bash`, `curl`, `jq`, `terraform`,
and the AWS CLI (`aws`). This is asserted at image build time, not left
implicit — a submission may depend on any of these tools for the read-only
inspection uses `instruction.md` permits without risking a verifier-side
"command not found" failure.
