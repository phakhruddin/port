# Model Summary

## Graded results

| Model | Graded runs | Scores | Mean | Best | Consistency note |
|---|---:|---|---:|---:|---|
| Claude Opus 4.8 | 4 | 63.64, 72.73, 63.64, 63.64 | **65.91** | 72.73 | Most consistent; recurring ALB reachability defect |
| Gemini 3.7 Flash | 3 of 4 | 81.82, 9.09, 63.64 | **51.52** | **81.82** | Best single model run, but high variance; one additional ungraded incomplete submission |
| GPT-5.6-sol | 4 | 9.09, 63.64, 9.09, 9.09 | **22.73** | 63.64 | Three runs stopped at deployment setup; one reached most infrastructure checks |
| Oracle artifacts supplied | 0 of 3 | — | — | — | All three stopped before grading due runtime/image startup failures |
| Successful Oracle baseline | 1 | 100.00 | 100.00 | 100.00 | 11/11 passed; no exception |

Means include only runs with an actual Harbor score. They are descriptive, not controlled benchmark statistics, because the runs span multiple task digests.

## Capability comparison

| Capability | Claude Opus 4.8 | Gemini 3.7 Flash | GPT-5.6-sol | Oracle baseline |
|---|---|---|---|---|
| Produce required file layout | Consistently yes | Usually; one empty/incomplete output | Yes | Yes |
| Initial infrastructure deployment | Consistently reached verifier | Mixed | Mixed | Pass |
| Network/storage topology | Passed when deployed | Passed when deployed | Passed in partial run | Pass |
| Authentication endpoint | Generally token setup succeeded | One invalid token URL | One invalid token URL | Pass |
| API behavior | Blocked by ALB DNS in all four runs | Passed in best run | Blocked or setup-failed | Pass |
| Stable redeployment | Passed once of four | Failed in two meaningful deployments | Failed in meaningful deployment | Pass |
| Drift repair | Usually passed | Best run failed Cognito update | Passed in meaningful deployment | Pass |
| Clean destruction | Passed when deployment completed | Passed when deployment completed | Passed in meaningful deployment | Pass |

## Fair comparison takeaway

For the `90812a88…` cohort, Gemini produced the strongest artifact at 81.82, while Claude produced two 63.64 results and GPT runs stopped at 9.09 due missing AWS CLI. For the `f17df02b…` cohort, Claude led at 72.73, while GPT and Gemini each scored 63.64. The evidence supports comparing failure modes within each digest more strongly than comparing global averages.
