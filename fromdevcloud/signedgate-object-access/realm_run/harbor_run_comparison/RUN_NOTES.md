# Individual Run Notes

## `429a1062` — GPT-5.6-sol — 9.09

Only the required-layout test passed. The deployment script looked for `/tmp/signedgate-submission/../config/config.json`; Harbor intentionally runs a copied submission, so the file was absent. The other ten errors cascade from this first failure.

## `b14c9519` — Gemini 3.7 Flash — 81.82

The strongest downloaded model run. Initial deployment, API behavior, declared infrastructure, network, storage, and destruction passed. Stable redeployment did not meet the verifier's plan expectation, and endpoint repair failed when Terraform attempted an unsupported Cognito `UpdateUserPool` operation.

## `84cc46f7` — Claude Opus 4.8 — 63.64

Seven infrastructure/lifecycle checks passed. The three behavior tests could not resolve the generated `*.elb.aws` hostname. Stable redeployment also failed because five required Terraform variables were supplied only as `-var` arguments inside `deploy.sh`, leaving the verifier's direct `terraform plan` without values (see `ORACLE_VS_CLAUDE_OPUS_4_8.md`). The verifier took about 17 minutes, reflecting long readiness waits.

## `320489e3` — GPT-5.6-sol — 63.64

Core infrastructure checks passed. Token acquisition returned HTTP 400 at `http://aws:4566/_aws/cognito-idp/oauth2/token`, producing three behavior setup errors. The stable redeployment assertion also failed.

## `7ee8e241` — Claude Opus 4.8 — 72.73

Eight tests passed, including stable redeployment and repair. All three behavior tests failed because the generated `*.elb.aws` hostname was unresolvable. Harbor separately recorded the Anthropic proxy-validation exit 86.

## `d6716edb` — Gemini 3.7 Flash — 63.64

Similar verifier shape to GPT run `320489e3`: HTTP 400 from the declared Cognito token URL caused three behavior setup errors, and stable redeployment failed. Seven other checks passed.

## `beaf8ec6` — Claude Opus 4.8 — 63.64

The same broad pattern as `84cc46f7`: unresolvable `*.elb.aws` URL caused three behavior failures, and stable redeployment failed. It also recorded the Anthropic proxy-validation exit 86 and spent about 19 minutes in the verifier.

## `42cdd865` — Oracle — no score

The verifier environment was created, but its `runtime-setup` service exited 2. Pytest never ran. This is an environment/runtime failure, not evidence that the golden solution failed its tests.

## `b8709ffe` — Gemini 3.7 Flash — 9.09

Deployment referenced `/workspace/contracts/schemas/manifest.schema.json`, which was unavailable in the verifier execution context. One layout test passed; ten tests errored through the shared deployment fixture.

## `e1970e10` — Gemini 3.7 Flash — no score

Verifier preflight rejected the submission because `deploy.sh` and `destroy.sh` were missing. Unlike the Oracle startup failures, this is attributable to the produced submission.

## `b875e635` — GPT-5.6-sol — 9.09

Terraform applied far enough to emit outputs, but `deploy.sh` then executed `aws`, which was not installed, and exited 127. The ten dependent tests errored.

## `a212596b` — Oracle — no score

Docker failed while pulling an image configuration with `unknown blob`. The verifier never ran, making this an image-distribution/platform failure.

## `2c909fe0` — Claude Opus 4.8 — 63.64

The generated `*.elb.localhost.localstack.cloud:4566` address did not resolve from the verifier, causing three behavior failures. Stable redeployment also failed because the refresh-disabled plan output did not include the expected metadata table. Harbor additionally recorded proxy-validation exit 86.

## `9218e434` — GPT-5.6-sol — 9.09

The deployment script explicitly checked for the AWS CLI and stopped with `Missing required command: aws`. One layout test passed and ten fixture-dependent tests errored.

## `fc4b947a` — Oracle — no score

The verifier `runtime-setup` service exited 1 before pytest. This is another pre-grading environment/runtime failure.

## Successful Oracle baseline — 100

Local job `rv-20260905T170541Z-f155bd` passed all 11 tests in 245.02 seconds, wrote score 100/reward 1.0, and recorded `exception_info: null`. It is the appropriate functional baseline when contrasting the downloaded model artifacts.
