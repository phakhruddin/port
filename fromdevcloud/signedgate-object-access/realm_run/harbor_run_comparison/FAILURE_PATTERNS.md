# Failure Patterns

## 1. Verifier-unreachable ALB URLs

Affected runs: `2c909fe0`, `7ee8e241`, `84cc46f7`, `beaf8ec6`.

The submissions exposed generated ALB DNS names such as `*.elb.aws` or `*.elb.localhost.localstack.cloud`. Those names did not resolve inside the separate verifier environment, so all three API behavior tests failed before RBAC logic was exercised.

This is a legitimate submission/interface defect: `manifest.json` must expose a verifier-reachable `alb.connect_url`. The successful Oracle baseline uses the shared service endpoint instead of an environment-local generated hostname.

## 2. Invalid Cognito token endpoints

Affected runs: `320489e3`, `d6716edb`.

Deployment and most infrastructure tests succeeded, but credential setup received HTTP 400 from the declared token URL. The behavior tests therefore errored while acquiring tokens. Examples included `/_aws/cognito-idp/oauth2/token` and `/<pool-id>/oauth2/token` forms that did not match the runtime contract.

## 3. Non-portable or unavailable deployment inputs

Affected runs:

- `429a1062`: resolved configuration as `../config/config.json`, which breaks after Harbor copies the submission.
- `b8709ffe`: deployment required a contract schema path that was unavailable to the copied verifier submission.
- `9218e434` and `b875e635`: submission depended on the `aws` executable, which was unavailable in that verifier image.

These are single setup defects with broad blast radius. Every test using the shared deployment fixture subsequently errored.

## 4. Terraform stability and recovery

Stable redeployment failed in `2c909fe0`, `320489e3`, `84cc46f7`, `beaf8ec6`, `d6716edb`, and `b14c9519`. The verifier expected a refresh-disabled plan that still referenced protected storage and did not imply unsafe replacement behavior. Common symptoms were missing expected metadata-table text or readiness/state drift.

Gemini run `b14c9519` also failed endpoint recovery because re-applying attempted an unsupported Cognito user-pool update. This is a distinct lifecycle defect even though its initial deployment and API behavior worked.

## 5. Incomplete submission

Run `e1970e10` reached verifier preflight without required `deploy.sh` and `destroy.sh`. No score was produced. This is a model-output failure, not a platform startup failure.

## 6. Claude proxy-validation exceptions

Runs `2c909fe0`, `7ee8e241`, and `beaf8ec6` ended with exit 86:

> Anthropic run completed without a proxied response; refusing unverified benchmark result

The verifier still graded the files left behind, so their numeric scores describe those artifacts. However, Harbor also recorded `UnknownApiError`, meaning model provenance/routing was not successfully validated. Keep this separate from the actual test failures. Claude run `84cc46f7` did not record this exception.

## 7. Oracle/platform startup failures

The three downloaded Oracle artifacts are not failed golden solutions:

- `42cdd865`: verifier `runtime-setup` exited 2.
- `a212596b`: image pull failed with `unknown blob`.
- `fc4b947a`: verifier `runtime-setup` exited 1.

None reached pytest or produced a score. By contrast, local Oracle run `rv-20260905T170541Z-f155bd` reached the verifier, passed 11/11, scored 100, and recorded no exception. This establishes that the current golden solution can pass when the environment starts correctly.

## Recommended reading order during triage

1. Check `result.json` for `exception_info` and verifier rewards.
2. Check the final pytest summary in `verifier/test-stdout.txt`.
3. Identify whether failures are `F` or fixture/setup `E`.
4. For deployment errors, inspect the first captured stderr block; later errors are usually repeats.
5. Use `exception.txt` only for trial/platform/agent failures that sit outside pytest.
