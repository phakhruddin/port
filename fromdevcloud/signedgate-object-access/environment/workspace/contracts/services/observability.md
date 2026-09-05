# Encryption and Observability

Create separate customer-managed KMS keys for objects and metadata. Enable key
rotation, set a deletion window of at least seven days, and create one alias
for each key.

Create `/ecs/<task-family>` as a managed CloudWatch log group with at least
seven days retention. Connect the API container through the `awslogs` driver.
Information-level authorization decisions must remain enabled, but secrets,
tokens and complete presigned URLs must not appear in logs.
