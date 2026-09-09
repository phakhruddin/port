# Cross-Model Run Comparison

Source: `fromdevcloud/signedgate-object-access/realm_run/**` (the
`ORACLE_VS_*.md` per-model comparisons and the `harbor_run_comparison/`
report set covering 15 downloaded Harbor artifact bundles plus one local
Oracle baseline). This file is our own synthesis of those reports, not a
copy. Read the originals for full evidence trails and file paths.

## Headline results

| Model | Graded runs | Scores | Mean | Best | Note |
|---|---:|---|---:|---:|---|
| Claude Opus 4.8 | 4 | 63.64, 72.73, 63.64, 63.64 | **65.91** | 72.73 | Most consistent; recurring ALB-reachability defect |
| Gemini 3.7 Flash | 3 of 4 | 81.82, 9.09, 63.64 | **51.52** | **81.82** (best single run overall) | High variance; one ungraded incomplete submission |
| GPT-5.6-sol | 4 | 9.09, 63.64, 9.09, 9.09 | **22.73** | 63.64 | Three runs stopped at deployment setup; see verifier-parity gotcha |
| Oracle (downloaded artifacts) | 0 of 3 | n/a | n/a | n/a | All three were platform/runtime startup failures, not solution failures |
| Oracle (local baseline) | 1 | 100.00 | 100.00 | 100.00 | 11/11 passed, no exception; proves the golden solution passes when the platform starts cleanly |

**Read this table carefully**: means mix runs across different task digests
and aren't a controlled benchmark statistic. The comparison-within-digest
view is more informative. For example, within the `90812a88…` digest
cohort, Gemini's 81.82 beat Claude's 63.64 and GPT's 9.09; within the
`f17df02b…` cohort, Claude's 72.73 led both others at 63.64.

## Failure patterns, by root cause

These are grouped by *actual defect*, not by model, since (per
`platform/scoring-and-gotchas.md`) the flat scoring formula makes several
independent runs look like distinct failures when they share one cause.

1. **Unresolvable ALB connect URL** (Claude, 4 runs). Submission published
   the real generated ALB hostname (`*.elb.aws`, `*.elb.localhost.localstack.cloud`)
   as `alb.connect_url` instead of the verifier-reachable service alias.
   Loses all 3 live API-behavior tests to DNS resolution failure before any
   RBAC/CRUD logic is exercised. This is a manifest-contract defect, not
   evidence the RBAC implementation itself is wrong.
2. **Invalid Cognito token endpoint** (2 runs). `token_url` didn't match the
   runtime contract's expected form (`/_aws/cognito-idp/oauth2/token` and
   `/<pool-id>/oauth2/token` variants observed), producing an HTTP 400
   during credential setup, so every behavioral test errors acquiring a
   token.
3. **Non-portable deployment inputs** (2 runs). One resolved config via a
   submission-relative path (`../config/config.json`) that breaks once
   Harbor copies the submission to its writable verifier location; one
   required a contracts-schema path unavailable after relocation. Both are
   genuine submission defects, and exactly the class `preflight.py` exists
   to catch cheaply.
4. **Verifier image missing the AWS CLI** (2 GPT-5.6 runs). Submissions used
   `aws ecs`/`aws elbv2` for read-only readiness checks, explicitly
   permitted by the contract and available in the agent environment, but
   the verifier's `tests/runtime/Dockerfile` only installs `boto3`. `deploy.sh`
   exits 127 on relocation, cascading into 10/11 tests erroring. **This is a
   verifier/task configuration bug**, not a demonstrated model defect; see
   `platform/scoring-and-gotchas.md`. The corresponding score (9.09) should
   not be read as "GPT-5.6 mostly failed this task."
5. **Terraform stability and recovery** (6 runs across all three models).
   `test_stable_redeployment` expects a `-refresh=false` plan with no
   creates/deletes/replacements; common causes of failure were required
   variables only supplied via `deploy.sh -var` flags (not persisted to an
   auto-loaded `.tfvars.json`, so the verifier's *standalone* `terraform
   plan` had nothing to work with) and genuine drift/readiness instability.
   One Gemini run additionally failed endpoint recovery when its apply
   triggered an incidental Cognito `UpdateUserPool` that Floci rejects
   outright (missing `AdvancedSecurityMode`), a real lifecycle defect, but
   compounded by an emulator limitation (see `platform/scoring-and-gotchas.md`).
6. **Incomplete submission** (1 run). Missing `deploy.sh`/`destroy.sh`
   entirely; never reached grading, a model-output failure distinct from a
   platform failure.
7. **Claude proxy-validation exceptions** (3 runs, overlapping with pattern 1).
   Harbor recorded `UnknownApiError`/exit 86 ("run completed without a
   proxied response") alongside an otherwise-valid graded score, a
   provenance/routing validation issue independent of the pytest result,
   worth tracking separately from actual test failures.
8. **Oracle/platform startup failures** (3 downloaded runs, 0 model-attributable).
   `runtime-setup` exiting non-zero, or an image pull failing with
   `unknown blob`; none reached pytest. These should never be read as "the
   golden solution scored 0"; they didn't run at all. The local Oracle
   baseline (100/100, 11/11, no exception) is the correct reference point.

## Per-model, versus Oracle, at a glance

| Capability | Claude Opus 4.8 | Gemini 3.7 Flash | GPT-5.6-sol |
|---|---|---|---|
| Required file layout | Consistently correct | Usually; one incomplete output | Correct |
| Initial deployment reaches verifier | Consistently | Mixed | Mixed (AWS CLI issue blocked otherwise-working deployments) |
| Network/storage topology (when deployed) | Pass | Pass | Pass (in the one run that got far enough) |
| API behavior | **Blocked in all 4 runs** by ALB DNS | Passed in best run | Blocked or setup-failed |
| Stable redeployment | Passed once of four | Failed (non-empty plan) | Not exercised (setup failure) |
| Drift repair | Usually passed | Failed (Cognito update rejected by Floci) | Passed once |
| Clean destruction | Passed whenever deployment completed | Passed whenever deployment completed | Passed once |

## Takeaways for future infra-scenario reviews

- **Don't compare raw scores across runs without checking the test-by-test
  breakdown first.** A 9.09 and a 63.64 can both reflect "one environment
  mismatch," just with different blast radii through the shared fixture.
- **The single highest-leverage detail across all three models was the
  manifest's connect URL.** Getting the emulator-reachable versus
  human-reachable endpoint distinction right (or wrong) determined whether
  *any* behavioral test could run at all, independent of RBAC correctness.
- **Recovery/idempotency bugs were the second most common category**, and
  several were compounded by real Floci emulation gaps rather than being
  pure solution defects. When triaging a future recovery-test failure,
  check `platform/scoring-and-gotchas.md`'s Floci-gotchas list before
  concluding the submission's Terraform is wrong.
- **Verifier/agent environment parity is a task-authoring risk, not just a
  model-performance variable.** The AWS CLI gap cost GPT-5.6 roughly 54
  points of apparent score for a defect that had nothing to do with its
  actual infrastructure competence.
