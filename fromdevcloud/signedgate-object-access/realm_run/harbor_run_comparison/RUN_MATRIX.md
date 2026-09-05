# Run Matrix

| Run ID | Agent / model | Task digest | Score | Pytest result | Classification | Primary cause |
|---|---|---|---:|---|---|---|
| `429a1062…` | GPT-5.6-sol | `3d7ee337…` | 9.09 | 1 passed, 10 errors | Cascading setup error | `deploy.sh` read `../config/config.json`; copied submission could not find it |
| `b14c9519…` | Gemini 3.7 Flash | `90812a88…` | **81.82** | 9 passed, 2 failed | Legitimate partial result | Unstable Terraform plan and failed Cognito update during endpoint repair |
| `84cc46f7…` | Claude Opus 4.8 | `90812a88…` | 63.64 | 7 passed, 4 failed | Legitimate partial result | Unresolvable ALB URL plus unstable redeployment/readiness issue |
| `320489e3…` | GPT-5.6-sol | `f17df02b…` | 63.64 | 7 passed, 1 failed, 3 errors | Legitimate partial result | Cognito token URL returned HTTP 400; stable plan assertion failed |
| `7ee8e241…` | Claude Opus 4.8 | `f17df02b…` | 72.73 | 8 passed, 3 failed | Partial result + agent exception | Unresolvable `*.elb.aws` URL; separate Anthropic proxy validation exit 86 |
| `d6716edb…` | Gemini 3.7 Flash | `f17df02b…` | 63.64 | 7 passed, 1 failed, 3 errors | Legitimate partial result | Incorrect Cognito token URL returned HTTP 400; stable plan assertion failed |
| `beaf8ec6…` | Claude Opus 4.8 | `90812a88…` | 63.64 | 7 passed, 4 failed | Partial result + agent exception | Unresolvable `*.elb.aws` URL plus unstable redeployment; proxy exit 86 |
| `42cdd865…` | Oracle | `44be53b9…` | — | Verifier did not run | Platform/runtime failure | Verifier `runtime-setup` container exited 2 |
| `b8709ffe…` | Gemini 3.7 Flash | `90812a88…` | 9.09 | 1 passed, 10 errors | Cascading setup error | Deployment depended on unavailable `/workspace/contracts/.../manifest.schema.json` |
| `e1970e10…` | Gemini 3.7 Flash | `28af2f18…` | — | Preflight failure | Invalid/incomplete submission | Required `deploy.sh` and `destroy.sh` were missing |
| `b875e635…` | GPT-5.6-sol | `90812a88…` | 9.09 | 1 passed, 10 errors | Cascading setup error | `deploy.sh` invoked unavailable `aws` command (exit 127) |
| `a212596b…` | Oracle | `f7839f2b…` | — | Verifier did not run | Platform image-pull failure | Docker image configuration pull failed with `unknown blob` |
| `2c909fe0…` | Claude Opus 4.8 | `f17df02b…` | 63.64 | 7 passed, 4 failed | Partial result + agent exception | Unresolvable LocalStack ALB hostname and stable-plan failure; proxy exit 86 |
| `9218e434…` | GPT-5.6-sol | `90812a88…` | 9.09 | 1 passed, 10 errors | Cascading environment/dependency error | Deployment explicitly stopped because `aws` was unavailable |
| `fc4b947a…` | Oracle | `b662c3df…` | — | Verifier did not run | Platform/runtime failure | Verifier `runtime-setup` container exited 1 |

## Comparable cohorts

Task digests matter: the runs were not all executed against the exact same task package.

| Task digest | Runs | Best graded result |
|---|---|---:|
| `90812a88…` | `b14c9519`, `84cc46f7`, `9218e434`, `b8709ffe`, `b875e635`, `beaf8ec6` | Gemini, 81.82 |
| `f17df02b…` | `2c909fe0`, `320489e3`, `7ee8e241`, `d6716edb` | Claude, 72.73 |
| Other digests | Five single-run task versions | Not suitable for direct within-version ranking |

Scores across different digests are useful operational evidence, but they are not a perfectly controlled model benchmark.
