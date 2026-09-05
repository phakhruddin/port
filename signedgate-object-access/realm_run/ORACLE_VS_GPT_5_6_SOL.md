# Oracle vs. GPT-5.6-sol Run Comparison

## Run summary

| Dimension | Oracle reference run | GPT-5.6-sol run |
|---|---|---|
| Result | Pass | Graded setup failure |
| Reported score | 100.00/100 | 9.09/100 |
| Pytest outcome | 11 passed, 0 failed | 1 passed, 10 setup errors |
| Reward | 1.0 | 0.0909 |
| Harbor/platform exception | None | None |
| Agent submission | Complete golden implementation | Complete scripts and Terraform; 44 resources created before deployment script failed |
| Immediate failure | None | `deploy.sh: line 34: aws: command not found` |
| Score interpretation | Representative | Mechanically correct, but not representative because the verifier lacks a tool available to the agent and permitted by the contract |

The oracle baseline is supported by multiple local 100/100 runs. The most
recent inspected baseline is
`jobs/rv-20260905T010050Z-8ffba1/signedgate-object-access__SnESGXc`.
The GPT-5.6 comparison uses portal artifact
`run-artifacts-b875e635-84cd-4b78-b71f-34ab463d7039`, trial
`materialized-task__A6gjQjZ`.

## Test-by-test mapping

| Test | Capability evaluated | Oracle | GPT-5.6-sol | Explanation and reported-score impact |
|---|---|---:|---:|---|
| `test_owner_crud_and_isolation` | Contributor CRUD, presigned URLs, sharing, cross-tenant isolation and admin access | Pass | Setup error | The session deployment fixture fails before the request is executed. No CRUD or isolation behavior is measured. |
| `test_viewer_cannot_create` | Viewer RBAC denial | Pass | Setup error | The API behavior is never reached because `deploy.sh` exits 127 when it calls the missing AWS CLI. |
| `test_key_confinement` | Tenant key normalization and traversal confinement | Pass | Setup error | No key-confinement request is made; this is a cascading fixture error. |
| `test_required_layout` | Required scripts and Terraform files | Pass | Pass | GPT-5.6 supplies `deploy.sh`, `destroy.sh`, and Terraform files, so the only test independent of the deployment fixture passes. |
| `test_terraform_configuration` | Terraform configuration validity | Pass | Setup error | Although Terraform successfully planned and applied 44 resources, the test itself depends on the failed deployment fixture and is reported as an error. |
| `test_manifest_identity` | Dynamic prefix/image identity and manifest topology fields | Pass | Setup error | GPT-5.6 generated a manifest in the agent environment, but verifier deployment stops before its manifest can be accepted. |
| `test_stable_redeployment` | Standalone Terraform stability and storage safety | Pass | Setup error | Never evaluated. |
| `test_private_network_graph` | Private ECS placement and S3 gateway endpoint routing | Pass | Setup error | Terraform created the relevant graph, but the live assertions never run. |
| `test_storage_security` | S3 versioning and public-access blocking | Pass | Setup error | Terraform declares these controls, but the live verifier assertions never run. |
| `test_endpoint_repair_preserves_storage` | Repair after deleting the S3 endpoint without replacing storage | Pass | Setup error | Never evaluated. |
| `test_clean_destroy` | Complete cleanup, including versioned storage | Pass | Setup error | Never evaluated because the initial deployment fixture did not complete. |

## Key implementation and environment differences

| Concern | Oracle implementation | GPT-5.6-sol implementation | Consequence |
|---|---|---|---|
| Runtime-config path | Uses `/workspace/config/config.json` | Uses `/workspace/config/config.json` | Both satisfy submission relocation requirements. |
| Infrastructure provisioning | Terraform reference solution | Terraform creates 44 resources successfully | GPT-5.6 gets substantially further than the reported score suggests. |
| Readiness inspection | Does not require AWS CLI in the verifier | Calls `aws ecs` and `aws elbv2` to confirm running tasks and healthy targets | GPT-5.6 depends on a tool missing from the separate verifier image. |
| Agent tool availability | AWS CLI is installed in the main environment | GPT-5.6 explicitly runs `aws --version` successfully before relying on it | The dependency is reasonable in the agent environment. |
| Verifier tool availability | Golden solution does not expose the omission | Verifier image installs `boto3` but not `awscli` | The same submitted script fails after relocation with exit 127. |
| Public contract | Permits AWS CLI for resource inspection and says to configure it for the endpoint | Uses AWS CLI only to inspect ECS/ELB state, not to create required infrastructure | GPT-5.6's use is within the stated contract. |
| Manifest connection URL | Uses `http://aws:80` | Uses `http://aws` | GPT-5.6 avoids the unresolvable ALB-hostname issue seen in the Claude run. |
| Network design | Private tasks, public ALB, S3 gateway endpoint | Declares the same core topology | Live verification is blocked before correctness can be confirmed. |

## Why GPT-5.6 received 9.09

The verifier counts passed tests, failed tests, and setup errors equally in
the denominator:

```text
passed = 1
failed = 0
errors = 10
total  = 11

score  = round(100 * 1 / 11, 2)
       = 9.09
reward = 0.0909
```

The arithmetic and reward files are valid, and Harbor completed without a
platform exception. However, the score is not a fair estimate of GPT-5.6's
task performance: ten results are repetitions of one environment mismatch,
not ten independently observed implementation failures.

## Root-cause analysis

GPT-5.6 checked AWS CLI availability in the main agent environment and got:

```text
aws-cli/1.46.1
```

Its deployment then used the CLI for allowed, read-only readiness checks:

- `ecs describe-services`;
- `elbv2 describe-target-health`;
- `ecs list-tasks`; and
- `ecs describe-tasks`.

The verifier uses a different Dockerfile. The main environment installs
`awscli`, but `tests/runtime/Dockerfile` installs `boto3` without installing
the `aws` executable. In the verifier, Terraform finishes creating all 44
resources and then the first readiness command fails:

```text
/tmp/signedgate-submission/deploy.sh: line 34: aws: command not found
```

Because `set -euo pipefail` is active, `deploy.sh` exits 127. The session-scoped
`deployment` fixture consequently errors for every dependent test.

## Assessment

This run is not a Harbor startup failure and the reward is syntactically
legitimate. It is nevertheless primarily a **task/verifier configuration
failure**, not a demonstrated GPT-5.6 infrastructure failure.

The public task says AWS CLI commands may inspect or exercise resources and
the architecture contract instructs the solver to configure AWS CLI for the
generated endpoint. Since AWS CLI is present while the model works, a solver
can reasonably depend on it. The separate verifier should provide the same
contractually permitted runtime dependency.

The existing evidence does not justify claiming the GPT-5.6 submission would
pass the remaining ten tests once AWS CLI is available. It only establishes
that those tests were not meaningfully executed. A rerun after fixing the
verifier image is required.

## Recommended task fix and rerun

1. Install `awscli` in `tests/runtime/Dockerfile`, matching the main
   environment, or explicitly remove AWS CLI from the public contract and
   preflight against its use. Matching the environments is the fairer fix.
2. Add an environment-parity check for every executable submissions are
   publicly allowed to use (`bash`, `curl`, `jq`, `terraform`, and `aws`).
3. Rerun GPT-5.6-sol after rebuilding the verifier image.
4. Treat the new run—not 9.09—as the meaningful model score. Review any
   remaining behavioral or lifecycle failures independently.

## Evidence

- GPT-5.6 verifier output:
  `/Users/bayawchik/Downloads/run-artifacts-b875e635-84cd-4b78-b71f-34ab463d7039/materialized-task__A6gjQjZ/verifier/test-stdout.txt`
- GPT-5.6 result:
  `/Users/bayawchik/Downloads/run-artifacts-b875e635-84cd-4b78-b71f-34ab463d7039/materialized-task__A6gjQjZ/result.json`
- GPT-5.6 submission:
  `/Users/bayawchik/Downloads/run-artifacts-b875e635-84cd-4b78-b71f-34ab463d7039/materialized-task__A6gjQjZ/artifacts/submission`
- Oracle result:
  `/Users/bayawchik/Project/micro1/devcloud/signedgate-object-access/jobs/rv-20260905T010050Z-8ffba1/signedgate-object-access__SnESGXc/result.json`
- Oracle verifier output:
  `/Users/bayawchik/Project/micro1/devcloud/signedgate-object-access/jobs/rv-20260905T010050Z-8ffba1/signedgate-object-access__SnESGXc/verifier/test-stdout.txt`
- Main environment definition:
  `/Users/bayawchik/Project/micro1/devcloud/signedgate-object-access/environment/Dockerfile`
- Separate verifier definition:
  `/Users/bayawchik/Project/micro1/devcloud/signedgate-object-access/tests/runtime/Dockerfile`
