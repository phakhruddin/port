# Oracle vs. Gemini 3.7 Flash Run Comparison

## Run summary

| Dimension | Oracle reference run | Gemini 3.7 Flash run |
|---|---|---|
| Result | Pass | Partial pass |
| Score | 100.00/100 | 81.82/100 |
| Tests | 11 passed, 0 failed | 9 passed, 2 failed |
| Reward | 1.0 | 0.8182 |
| Platform exception | None | None |
| Grading status | Complete and valid | Complete and valid |
| Primary difference | Stable no-op planning and successful targeted drift repair | Provider/emulator read-back drift causes a non-empty plan and a failed Cognito update during endpoint repair |

The oracle baseline is supported by multiple local 100/100 runs. The most
recent inspected baseline is
`jobs/rv-20260905T010050Z-8ffba1/signedgate-object-access__SnESGXc`.
The Gemini comparison uses portal artifact
`run-artifacts-b14c9519-570c-402d-bc70-e2ee741955df`, trial
`materialized-task__Fi8vny3`.

## Test-by-test mapping

| Test | Capability evaluated | Oracle | Gemini 3.7 Flash | Explanation and score impact |
|---|---|---:|---:|---|
| `test_owner_crud_and_isolation` | Contributor CRUD, presigned URLs, sharing, cross-tenant isolation and admin access | Pass | Pass | Gemini exposes a verifier-reachable API and satisfies the tested CRUD, sharing, isolation, and administrative behavior. |
| `test_viewer_cannot_create` | Viewer RBAC denial | Pass | Pass | The viewer token is correctly denied file creation. |
| `test_key_confinement` | Tenant key normalization and traversal confinement | Pass | Pass | Generated object keys remain under the tenant prefix and remove traversal components. |
| `test_required_layout` | Required scripts and Terraform files | Pass | Pass | Both submissions contain executable deployment/destruction scripts and Terraform sources. |
| `test_terraform_configuration` | Terraform configuration validity | Pass | Pass | Gemini's Terraform configuration validates successfully. |
| `test_manifest_identity` | Dynamic prefix/image identity and manifest topology fields | Pass | Pass | Gemini reads `/workspace/config/config.json` and reports the required runtime identity and topology. |
| `test_stable_redeployment` | Standalone, non-refresh Terraform plan and storage stability | Pass | Fail | Gemini's plan exits with code 2, indicating proposed changes. The verifier's stability guard also cannot find the metadata-table identity in that change plan. The deployment is therefore not intrinsically no-op stable. |
| `test_private_network_graph` | Private ECS placement and S3 gateway endpoint routing | Pass | Pass | Gemini uses private ECS networking, disables public IPs, and attaches the S3 gateway endpoint to the private route tables. |
| `test_storage_security` | S3 versioning and public-access blocking | Pass | Pass | Bucket versioning and all public-access-block controls are enabled. |
| `test_endpoint_repair_preserves_storage` | Repair after deleting the S3 endpoint without replacing storage | Pass | Fail | Terraform recreates the deleted endpoint, but the same apply also attempts an emulator-induced Cognito update. Floci rejects `UpdateUserPool` because `AdvancedSecurityMode` is absent, causing `deploy.sh` to exit 1 before completing the repair workflow. |
| `test_clean_destroy` | Complete resource cleanup, including versioned storage | Pass | Pass | Gemini empties versioned objects and leaves Terraform state empty after destruction. |

## Key implementation differences

| Concern | Oracle implementation | Gemini 3.7 Flash implementation | Consequence |
|---|---|---|---|
| Logical ALB URL | Keeps the generated ALB DNS name in `alb.url` and `alb.dns_name` | Same | Both correctly describe the logical load balancer. |
| Verifier connection URL | Uses the reachable AWS-compatible endpoint (`http://aws:80`) | Uses `http://aws` | Both pass all live API behavior tests. |
| Runtime configuration | Reads the absolute runtime config and creates automatically available Terraform inputs | Terraform reads `/workspace/config/config.json` directly | Both support relocated submissions and direct Terraform commands. |
| CRUD and RBAC | Passes owner, viewer, sharing, cross-tenant and admin checks | Passes the same checks | Gemini demonstrates materially complete application-facing behavior. |
| No-op plan | Produces a verifier-acceptable stable plan | Returns detailed-exit code 2 with proposed changes | Gemini loses the stable-redeployment test. |
| Cognito drift handling | Avoids an invalid `UpdateUserPool` during recovery | Ignores `device_configuration` and `user_pool_add_ons`, but not the observed `email_configuration` drift | Gemini's recovery apply reaches an unsupported Floci update path and exits unsuccessfully. |
| S3 read-back drift | Remains acceptable to the verifier | Recovery output shows an in-place S3 tag reconciliation | This contributes unnecessary plan noise and weakens idempotency. |
| Endpoint recovery | Restores the deleted endpoint and finishes successfully | Recreates the endpoint, then fails while updating Cognito | The infrastructure repair begins, but the required deployment transaction does not complete. |
| destroy | Removes all managed infrastructure and versioned objects | Explicitly empties versions/delete markers and destroys resources | Both pass cleanup. |

## Why Gemini received 81.82

The verifier gives each collected pytest result equal weight. The category
percentages in `tests/suite/obligations.yaml` are not used in the final score.

```text
passed = 9
failed = 2
total  = 11

score  = round(100 * 9 / 11, 2)
       = 81.82
reward = 0.8182
```

This is a legitimate score, not a Harbor or Realm startup failure. Both
failures concern lifecycle robustness rather than the core CRUD/RBAC path.
The run provides positive evidence that Gemini's networking, storage,
identity, connectivity, presigned operations, and cleanup work. It does not
satisfy the requirement that repeated deployment be stable and reliably
repair drift.

## Detailed failure analysis

### Stable-plan failure

The verifier executes a standalone plan with `-refresh=false` and
`-detailed-exitcode`. Gemini returns code 2, meaning Terraform proposes
changes instead of producing a no-op plan. Because the resulting plan does
not contain the metadata-table name required by the verifier's storage-safety
guard, the test fails.

The later recovery output confirms related provider/emulator normalization
noise: Terraform wants to reconcile Cognito email configuration and S3 tags.
Gemini handled some Floci read-back differences, but not all of the fields
observed by the verifier.

### Recovery failure

The recovery test deletes the managed S3 endpoint and reruns `deploy.sh`.
Gemini's Terraform plan correctly identifies and recreates that endpoint.
However, the apply also proposes unrelated in-place changes:

- Cognito user-pool email configuration; and
- S3 bucket tag normalization.

Floci rejects the Cognito update with:

```text
missing required field, UpdateUserPoolInput.UserPoolAddOns.AdvancedSecurityMode
```

Terraform therefore returns nonzero, `deploy.sh` fails, and the verifier
cannot accept the recovery even though endpoint creation itself completed.

## Minimal changes that would close the gap

1. Make the post-deployment `terraform plan -refresh=false` a true no-op by
   aligning configuration with the provider's stored representation.
2. Suppress or explicitly normalize the known Floci Cognito read-back fields,
   including the observed `email_configuration` drift, so endpoint repair
   does not trigger an unrelated `UpdateUserPool` call.
3. Eliminate the observed S3 tag reconciliation noise where possible.
4. Rerun the endpoint-deletion scenario and require `deploy.sh` to return zero,
   regenerate the manifest, preserve the bucket/table identities, and expose
   the replacement endpoint ID.

## Evidence

- Gemini verifier output:
  `/Users/bayawchik/Downloads/run-artifacts-b14c9519-570c-402d-bc70-e2ee741955df/materialized-task__Fi8vny3/verifier/test-stdout.txt`
- Gemini result:
  `/Users/bayawchik/Downloads/run-artifacts-b14c9519-570c-402d-bc70-e2ee741955df/materialized-task__Fi8vny3/result.json`
- Gemini submission:
  `/Users/bayawchik/Downloads/run-artifacts-b14c9519-570c-402d-bc70-e2ee741955df/materialized-task__Fi8vny3/artifacts/submission`
- Oracle result:
  `jobs/rv-20260905T010050Z-8ffba1/signedgate-object-access__SnESGXc/result.json`
- Oracle verifier output:
  `jobs/rv-20260905T010050Z-8ffba1/signedgate-object-access__SnESGXc/verifier/test-stdout.txt`
