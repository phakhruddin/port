# Scoring Mechanics and Known Platform Gotchas

## Scoring is flat, not weighted

Tasks ship an `obligations.yaml` with per-category point weights (e.g. for
`signedgate-object-access`: RBAC/isolation 25, presigned CRUD 20, networking
20, security/encryption 15, recovery 12, observability/cleanup 8, summing
to 100). **The verifier does not currently apply these weights.** The actual
score, computed in `conftest.py`'s `pytest_sessionfinish`, is:

```text
score = round(100 * passed / (passed + failed + errors), 2)
```

Every collected pytest result, pass, assertion failure, and fixture/setup
error alike, counts as one unit in the denominator. Two consequences worth
flagging in any discussion of "how good was this run":

1. **A category-weighted rubric exists in the task's intent but not in its
   grading.** A run that nails RBAC (25 pts of intent) but fails one
   lifecycle check scores identically to a run that fails RBAC but nails
   lifecycle. Don't read the numeric score as evidence about *which*
   capability is weak without checking the test-by-test breakdown.
2. **Setup errors are not distinguished from behavioral failures in the
   score**, even though they mean something very different: a `failed` (`F`)
   reached an assertion; an `error` (`E`) generally means the shared
   `deployment` fixture (or another fixture) didn't complete. Because most
   tests in this suite depend on one session-scoped `deployment` fixture, a
   single early failure (bad `alb.connect_url`, a missing binary, a bad
   manifest path) cascades into most of the ten dependent tests erroring,
   inflating the appearance of breadth of failure. Always check whether a
   low score is "one root cause, ten cascaded errors" or "ten independently
   demonstrated defects" before comparing runs.

## Agent/verifier environment parity is not guaranteed

The agent's Dockerfile and the verifier's Dockerfile (`tests/runtime/Dockerfile`)
are maintained separately and can drift. Observed instance: the task
contract explicitly permits and even directs use of the AWS CLI for
read-only inspection, and the agent environment installs `awscli`, but the
verifier environment installed only `boto3`, no `aws` executable. A
submission that reasonably depends on a contractually-permitted tool works
right up until the verifier relocates and re-runs it, then fails with `exit
127` on every dependent test. This reads, at a glance, like a submission
defect; it is a verifier/task configuration bug. **Before attributing a
cascading setup failure to the submission, check whether the failing
command is available in the *verifier's* image, not just the agent's.**

General mitigation for future task reviews: enumerate every executable the
public contract says a submission may use, and confirm it's installed in
both Dockerfiles.

## Floci emulation gaps that a correct solution must route around

Floci is a real (non-mocked, for ECS) emulator, not just a stub, but it
doesn't implement the full AWS surface faithfully. Specific gaps seen in
this task:

- **No `ModifyVpcEndpoint` support.** A route-table-association change on an
  existing S3 gateway endpoint can't be applied in place the way real AWS
  would; recovery flows that expect Terraform to reconcile this need to
  route around it (e.g. by recreating the endpoint rather than modifying it).
- **Read-back drift on refresh.** Floci omits or defaults several fields
  AWS would normally echo back, so a plain `terraform plan` (with refresh)
  can show spurious in-place changes that aren't real drift. The Oracle
  solution's own stability test uses `terraform plan -refresh=false` for
  exactly this reason: it's testing the *declared* configuration's
  self-consistency, not asserting the live provider read-back matches
  byte-for-byte.
- **`UpdateUserPool` requires `AdvancedSecurityMode`.** If Terraform's
  planned update to a Cognito user pool doesn't explicitly carry
  `UserPoolAddOns.AdvancedSecurityMode`, Floci rejects the call outright.
  This surfaced as a real failure mode: a solution that triggers *any*
  incidental Cognito in-place update (e.g. from unmanaged
  `email_configuration` drift) during an unrelated recovery flow can fail
  the entire `deploy.sh` run on this one emulator limitation, even though
  the actual repair logic (e.g., recreating a deleted VPC endpoint) worked.

Any Terraform solution against this platform should be written to produce
a **true no-op plan** on repeated apply, not just "no destructive changes"
but no proposed changes at all, specifically to avoid triggering emulator
codepaths that aren't fully implemented.

## The `alb.connect_url` vs `alb.dns_name`/`alb.url` distinction

The manifest schema requires an `alb.connect_url`, and it is tempting to
populate it with the same value as the "real" ALB DNS name
(`alb.dns_name`/`alb.url`) since that's what a real client would use. In
this emulated environment, the generated ALB hostname (e.g.
`*.elb.aws` or `*.elb.localhost.localstack.cloud`) is **not resolvable from
inside the separate verifier container**; only the shared service alias
(`http://aws:80` in this task) is. A manifest that conflates these two
fields loses every live API-behavior test to a DNS failure, independent of
whether the underlying RBAC/CRUD implementation is correct. When reviewing
a failing run, check whether behavioral failures are really connectivity
failures in disguise before concluding the application logic is wrong.

## Terraform inputs must be persisted, not just passed to `apply`

The verifier runs `terraform plan` **standalone** (via `tests/suite/test_lifecycle.py`'s
`test_stable_redeployment`), not through the submission's `deploy.sh`. Any
required Terraform variable that `deploy.sh` only supplies via `-var`/`-var-file`
flags to `terraform apply` will be **undefined** for that standalone plan
and cause it to fail outright (`terraform plan` exits 1 rather than 0/2).
The robust pattern (used by the Oracle solution) is to write required values
to an auto-loaded variable file (e.g. `infra/config.auto.tfvars.json`)
during `deploy.sh`, so any direct `terraform` invocation against that
directory has everything it needs without re-deriving flags.

## Preflight is cheap and runs before any cloud spend

`tests/preflight.py` is a fast, pre-deployment sanity gate (checks required
files exist, and that any `config/config.json` reference is the exact
required absolute path). A submission that fails preflight never reaches
the verifier's pytest suite at all. This is a distinct failure class from
a graded run and should not be scored or discussed as if it were a 0%
functional result; it's closer to "invalid submission," comparable to the
"Incomplete submission" pattern seen when `deploy.sh`/`destroy.sh` are
missing outright.
