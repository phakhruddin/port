# Test Outcome Matrix

Legend: ✅ passed, ❌ failed assertion/behavior, ⚠️ setup error, — verifier did not produce test results.

| Run | Layout | Owner CRUD | Viewer deny | Key confinement | TF config | Manifest | Stable redeploy | Network | Storage | Repair | Destroy |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `b14c9519` Gemini | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| `7ee8e241` Claude | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `2c909fe0` Claude | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `84cc46f7` Claude | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `beaf8ec6` Claude | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `320489e3` GPT | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `d6716edb` Gemini | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `429a1062` GPT | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `9218e434` GPT | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `b8709ffe` Gemini | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `b875e635` GPT | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| `e1970e10` Gemini | — | — | — | — | — | — | — | — | — | — | — |
| Downloaded Oracle ×3 | — | — | — | — | — | — | — | — | — | — | — |
| Successful Oracle baseline | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## What the matrix shows

- Infrastructure declaration, network topology, storage security, repair, and destruction frequently passed once deployment completed.
- The most common model-level gap was the runtime access surface: either an invalid/unresolvable ALB URL or an invalid Cognito token URL.
- A 9.09 score here normally means only `test_required_layout` passed before the shared deployment fixture failed. It should not be read as ten separately evaluated feature failures.
- The successful Oracle baseline completed all 11 tests in 245.02 seconds and scored 100.
