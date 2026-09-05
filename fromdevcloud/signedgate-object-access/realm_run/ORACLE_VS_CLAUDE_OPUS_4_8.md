# Oracle vs. Claude Opus 4.8 Run Comparison

## Run summary

| Dimension | Oracle reference run | Claude Opus 4.8 run |
|---|---|---|
| Result | Pass | Partial pass |
| Score | 100.00/100 | 63.64/100 |
| Tests | 11 passed, 0 failed | 7 passed, 4 failed |
| Reward | 1.0 | 0.6364 |
| Platform exception | None | None |
| Grading status | Complete and valid | Complete and valid |
| Primary difference | Uses verifier-reachable ALB connection URL and persistent Terraform inputs | Publishes an unresolvable ALB hostname and supplies Terraform inputs only through `deploy.sh` |

The oracle baseline is supported by several local 100/100 runs. The most
recent inspected baseline is
`jobs/rv-20260905T010050Z-8ffba1/signedgate-object-access__SnESGXc`.
The Claude comparison uses portal artifact
`run-artifacts-84cc46f7-e4f3-498f-9766-26ce11a76a42`, trial
`materialized-task__L78A6cN`.

## Test-by-test mapping

| Test | Capability evaluated | Oracle | Claude Opus 4.8 | Explanation and score impact |
|---|---|---:|---:|---|
| `test_owner_crud_and_isolation` | Contributor CRUD, presigned URLs, sharing, cross-tenant isolation and admin access | Pass | Fail | Claude sets `alb.connect_url` to the synthetic `*.elb.aws` name. That hostname cannot resolve in the verifier, so the API is never reached. |
| `test_viewer_cannot_create` | Viewer RBAC denial | Pass | Fail | Same connection failure. This does not establish that Claude's viewer policy is wrong; the request never reaches SignedGate. |
| `test_key_confinement` | Tenant key normalization and traversal confinement | Pass | Fail | Same connection failure. The submitted API behavior is not exercised. |
| `test_required_layout` | Required scripts and Terraform files | Pass | Pass | Both submissions contain executable `deploy.sh`, `destroy.sh`, and Terraform configuration. |
| `test_terraform_configuration` | Terraform configuration validity | Pass | Pass | Claude's Terraform validates successfully after deployment. |
| `test_manifest_identity` | Dynamic prefix/image identity and manifest topology fields | Pass | Pass | Claude generates the required manifest values and reports two tasks and the required subnet sets. |
| `test_stable_redeployment` | Standalone, non-refresh Terraform plan and storage stability | Pass | Fail | Claude declares five required variables but supplies them only as `-var` arguments inside `deploy.sh`. The verifier's direct `terraform plan` has no values for them and exits 1. |
| `test_private_network_graph` | Private ECS placement and S3 gateway endpoint routing | Pass | Pass | Claude creates a gateway endpoint on the private route tables and disables public IP assignment for ECS. |
| `test_storage_security` | S3 versioning and public-access blocking | Pass | Pass | Claude enables bucket versioning and all public-access-block settings. |
| `test_endpoint_repair_preserves_storage` | Repair after deleting the S3 endpoint without replacing storage | Pass | Pass | Claude's repeated deployment restores the endpoint and retains the bucket and metadata table identities. |
| `test_clean_destroy` | Complete resource cleanup, including versioned storage | Pass | Pass | Claude's destroy process empties/removes the managed resources and leaves Terraform state empty. |

## Key implementation differences

| Concern | Oracle implementation | Claude Opus 4.8 implementation | Consequence |
|---|---|---|---|
| Logical ALB URL | Preserves the generated ALB DNS value in `alb.url`/`alb.dns_name` | Preserves the generated ALB DNS value | Both correctly describe the logical ALB. |
| Verifier connection URL | Sets `alb.connect_url` to `http://<aws_endpoint_host>:80`, which is reachable as `http://aws:80` | Sets `alb.connect_url` equal to `http://<generated-alb>.elb.aws` | Claude loses three behavioral tests to DNS resolution failure. |
| Readiness probe | Uses the same reachable manifest connection path | Uses `curl --resolve` during deployment, but does not expose that working route in the manifest | Claude proves readiness internally while giving the verifier a URL it cannot use. |
| Runtime Terraform inputs | Writes dynamic values to `infra/config.auto.tfvars.json` | Builds a `TF_VARS` array and passes it only to `terraform apply` | Oracle supports direct Terraform commands; Claude's direct plan lacks required inputs. |
| Runtime-config path | Uses `/workspace/config/config.json` | Uses `/workspace/config/config.json` | Both satisfy the relocation requirement. |
| Recovery | Re-applies Terraform while retaining storage | Re-applies Terraform while retaining storage | Both pass endpoint recovery. |
| Destruction | Removes all managed infrastructure and versioned objects | Explicitly empties versions/delete markers and destroys Terraform resources | Both pass cleanup. |

## Why Claude received 63.64

The verifier currently gives every collected pytest result equal weight. It
does not apply the category percentages in `tests/suite/obligations.yaml` to
the final calculation.

```text
passed = 7
failed = 4
total  = 11

score  = round(100 * 7 / 11, 2)
       = 63.64
reward = 0.6364
```

This is a legitimate score for the current verifier. However, three of the
four failed tests share one connectivity defect, so the score should not be
interpreted as three independently demonstrated RBAC defects. The run proves
that Claude built much of the required infrastructure, but it does not prove
that its CRUD/RBAC behavior works because the verifier could not connect to
the API.

## Minimal changes that would close the gap

1. Keep the generated ALB hostname in `alb.dns_name` and `alb.url`, but set
   `alb.connect_url` to the verifier-reachable endpoint, normally
   `http://aws:80` for this environment.
2. Persist dynamically read runtime values in `infra/config.auto.tfvars.json`
   (or an equivalent automatically loaded Terraform variable file) so direct
   `terraform plan` commands work without `deploy.sh` supplying `-var` flags.
3. Rerun all behavioral tests. Passing them is still necessary before claiming
   the Claude implementation satisfies CRUD, RBAC, sharing, and key isolation.

## Evidence

- Claude verifier output:
  `/Users/bayawchik/Downloads/run-artifacts-84cc46f7-e4f3-498f-9766-26ce11a76a42/materialized-task__L78A6cN/verifier/test-stdout.txt`
- Claude result:
  `/Users/bayawchik/Downloads/run-artifacts-84cc46f7-e4f3-498f-9766-26ce11a76a42/materialized-task__L78A6cN/result.json`
- Claude submission:
  `/Users/bayawchik/Downloads/run-artifacts-84cc46f7-e4f3-498f-9766-26ce11a76a42/materialized-task__L78A6cN/artifacts/submission`
- Oracle result:
  `jobs/rv-20260905T010050Z-8ffba1/signedgate-object-access__SnESGXc/result.json`
- Oracle verifier output:
  `jobs/rv-20260905T010050Z-8ffba1/signedgate-object-access__SnESGXc/verifier/test-stdout.txt`
