# Encryption and Observability

Create separate customer-managed KMS keys for objects and metadata. Enable key
rotation, set a deletion window of at least seven days, and create one alias
for each key.

Create `/ecs/<task-family>` as a managed CloudWatch log group with at least
seven days retention. Connect the API container through the `awslogs` driver.
Information-level authorization decisions must remain enabled, but secrets,
tokens and complete presigned URLs must not appear in logs.

This is directly verified, not just stated: `tests/suite/test_recovery.py::test_log_hygiene`
scans the API task's captured log output for bearer tokens, client secrets,
and full presigned URL query strings, and fails if any are present. The
supplied API image's request-logging middleware already satisfies this
(it logs only a request ID, method, path and status code) — do not add
additional logging elsewhere in your infrastructure (for example, an ALB
access-log configuration that captures full query strings) that would
reintroduce this class of leak.
