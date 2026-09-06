# Identity and IAM

Create one Cognito user pool, a resource server named `signedgate`, and four
confidential clients: `viewer`, `contributor-a`, `contributor-b` and `admin`.
Each client uses the client-credentials flow. The two contributor clients both
receive only `signedgate/contributor`; the other clients receive exactly their
matching `signedgate/viewer` or `signedgate/admin` scope. Two contributor
identities are required so the verifier can test cross-tenant isolation.

Create distinct ECS execution and API task roles. The execution role may write
only to the API log group. The API role may perform the object CRUD operations
required for presigning only on the managed bucket, metadata operations only
on the managed table, KMS cryptographic operations only on the two managed
keys, and CloudWatch log writes only on the API group. Avoid wildcard actions.

## Emulator note: avoid incidental Cognito updates during recovery

The emulated identity provider rejects `UpdateUserPool` calls that omit
`UserPoolAddOns.AdvancedSecurityMode`, even when the update being attempted
is unrelated to security configuration. A user pool whose attributes are
left fully managed by Terraform can pick up incidental drift (for example, in
default `email_configuration` values) that triggers exactly this kind of
call during an otherwise-unrelated recovery `apply` — failing the entire
`deploy.sh` run on a call your solution never intended to make.

If you observe this failure mode, constrain which attributes Terraform
actively reconciles on the user pool (for example, with a `lifecycle {
ignore_changes = [...] }` block covering fields the platform does not
round-trip cleanly) rather than trying to supply a value that satisfies the
emulator's validation. The reference solution does this — see
`solution/infra/identity.tf`.
