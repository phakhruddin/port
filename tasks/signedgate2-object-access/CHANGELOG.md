# Changelog: signedgate-object-access to signedgate2-object-access

This task is a ground-up revision of `fromdevcloud/signedgate-object-access`
(v0.1.19), driven directly by the findings in `harbor-analysis/` in this
repository. Each change below cites the specific finding it addresses so the
rationale doesn't need to be reconstructed later.

## Fixed at the platform level

### 1. Scoring is now weighted by category, computed per-category

**Finding:** `harbor-analysis/platform/scoring-and-gotchas.md` § "Scoring is
flat, not weighted." v1 shipped an `obligations.yaml` rubric that the
verifier never applied; the actual score was `100 * passed / total` across
all 11 tests, unweighted, with setup errors counted identically to
behavioral failures.

**Fix:** `tests/suite/conftest.py` now maps every test to a category via
`CATEGORY_BY_TEST`, and `pytest_sessionfinish` computes
`sum(weight * passed_in_category / total_in_category for category)`. A
category that never ran (because a shared fixture failed) scores zero for
*that category only*, instead of the failure being smeared proportionally
across the whole flat ratio. The mapping is documented in `reasoning.md` and
must be kept in sync with the code.

### 2. Verifier/agent tool parity is asserted at image build time

**Finding:** `harbor-analysis/platform/scoring-and-gotchas.md` § "Agent/verifier
environment parity is not guaranteed." A GPT-5.6-sol run lost ~54 points
because the verifier's Dockerfile installed `boto3` but not `awscli`, even
though the public contract explicitly permits AWS CLI use and the agent
environment provides it.

**Fix:** `tests/runtime/Dockerfile` installs the same tool set as
`environment/Dockerfile` (`bash`, `curl`, `jq`, `terraform`, `awscli`) and
fails the image build itself if any of them is missing
(`for tool in bash curl jq terraform aws; do command -v "$tool" >/dev/null; done`).
`instruction.md` now states this parity as a contract guarantee, so a
submission can rely on any permitted tool without defensively checking for
its absence.

### 3. `alb.connect_url` is now an explicit, separately-tested contract

**Finding:** `harbor-analysis/cases/signedgate-object-access/model-run-comparison.md`:
across all three evaluated models, the single highest-leverage defect was
conflating the ALB's real generated DNS name with the verifier-reachable
connection endpoint. This cost Claude Opus 4.8 three behavioral tests in
every one of its four graded runs, independent of whether its RBAC/CRUD
logic was correct.

**Fix:**
- `instruction.md` and `environment/workspace/contracts/architecture.md`
  spell out the distinction between `alb.dns_name`/`alb.url` (informational,
  real DNS) and `alb.connect_url` (must be verifier-reachable) with an
  explicit warning against conflating them.
- `environment/workspace/contracts/schemas/manifest.schema.json` documents
  both fields with `description` text stating this distinction inline.
- `tests/suite/test_declared.py` gained `test_manifest_connectivity`, a fast
  check that resolves and probes `alb.connect_url` *before* the full
  behavioral suite runs, with a failure message that names the likely
  mistake directly instead of surfacing as three unrelated RBAC failures.

### 4. Terraform input persistence is a named requirement, not an inferred one

**Finding:** `harbor-analysis/cases/signedgate-object-access/reference-solution.md`
and `model-run-comparison.md`: the verifier runs `terraform plan` standalone
against `infra/`, not through `deploy.sh`. A submission that only supplies
required variables via `-var` flags inside `deploy.sh` passes deployment but
fails that standalone plan, and previously this only surfaced as an opaque
`test_stable_redeployment` failure.

**Fix:** `instruction.md` states the requirement directly ("every dynamic
Terraform input must be persisted to an automatically loaded variable
file"). `tests/suite/test_lifecycle.py`'s `test_stable_redeployment` failure
message now names this specific cause when the plan fails outright (exit
code 1) rather than showing changes (exit code 2).

### 5. Floci's Cognito/VPC-endpoint emulation gaps are documented and routed around

**Finding:** `harbor-analysis/platform/scoring-and-gotchas.md` § "Floci
emulation gaps..." A Gemini 3.7 Flash run's recovery flow correctly
recreated a deleted S3 endpoint, but the same `apply` also proposed an
incidental Cognito `UpdateUserPool` call that Floci rejects
(`missing required field, UpdateUserPoolInput.UserPoolAddOns.AdvancedSecurityMode`),
failing the whole deployment on an emulator limitation unrelated to the
actual repair logic.

**Fix:** `reasoning.md` documents this and the two related Floci gaps
(`ModifyVpcEndpoint`, refresh read-back drift) as known platform behavior.
`solution/infra/identity.tf` adds a `lifecycle { ignore_changes = [...] }`
block on the Cognito user pool for fields Floci does not round-trip
cleanly, as the reference pattern for avoiding this failure mode.

## Closed test-coverage gaps

Reading the full v1 suite against `instruction.md`'s nine required outcomes
surfaced three outcomes that were stated as requirements but never actually
exercised by any test:

| Gap | Required outcome | New test |
|---|---|---|
| A viewer could be denied creation, but no test ever confirmed a viewer **could** read a file genuinely shared with them | #6 | `test_viewer_can_read_shared_file` (`tests/suite/test_rbac.py`) |
| Signature tampering / unsigned requests were required to be rejected but never submitted | #7 | `test_unsigned_request_rejected`, `test_signature_tamper_rejected` (`tests/suite/test_rbac.py`) |
| Log hygiene (no secrets/tokens/full presigned URLs in logs) was a stated requirement with zero automated verification | #9 | `test_log_hygiene` (`tests/suite/test_recovery.py`) |

`test_owner_crud_and_isolation` (v1) was also split into smaller,
single-purpose tests: `test_contributor_can_create_and_upload` and
`test_owner_can_download_and_delete` (both `presigned_crud`), plus
`test_cross_tenant_read_denied` and `test_admin_can_access_any_file` (both
`rbac_and_isolation`, `tests/suite/test_behavior.py`). This way a failure
names the specific capability that broke, and each test maps cleanly to
one scoring category instead of one test straddling two categories' worth
of assertions.

## Unchanged from v1

The core architecture (VPC/subnet/route-table layout, ALB to ECS to
DynamoDB/S3 topology, KMS keys, IAM scoping, Cognito client-credentials
model) is unchanged. v1's design was sound; the defects were in the
platform's contract clarity, tooling, and grading, not in what was being
asked of a solver. The supplied API application
(`environment/application/app.py`) is carried forward without modification.
