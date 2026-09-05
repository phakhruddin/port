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
