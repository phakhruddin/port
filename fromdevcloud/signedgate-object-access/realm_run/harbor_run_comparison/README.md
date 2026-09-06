# Harbor Run Comparison

This report set compares the 15 Harbor artifact bundles collected under
`/Users/bayawchik/Downloads/harbor-run/`.

## Start here

- [RUN_MATRIX.md](RUN_MATRIX.md) — one-row-per-run executive comparison.
- [TEST_MATRIX.md](TEST_MATRIX.md) — test-level pass/fail/error map for graded runs.
- [FAILURE_PATTERNS.md](FAILURE_PATTERNS.md) — recurring root causes and how to interpret them.
- [MODEL_SUMMARY.md](MODEL_SUMMARY.md) — model-level consistency and score comparison.
- [RUN_NOTES.md](RUN_NOTES.md) — concise evidence-backed notes for every run.

## Interpretation rules

- **Graded model failure** means the verifier ran and produced a score.
- **Cascading setup error** means one deployment failure caused many tests to error; it is not ten independent defects.
- **Platform failure** means Harbor failed before a score existed. These runs should not be treated as zero-score model results.
- A pytest **failure** (`F`) reached an assertion or behavioral check. A pytest **error** (`E`) generally means fixture or deployment setup did not complete.
- The successful Oracle baseline is the local run `rv-20260905T170541Z-f155bd`. It is included for comparison but is not one of the 15 downloaded bundles.

## Headline

The highest scored downloaded model run is Gemini 3.7 Flash at **81.82%**. Claude Opus 4.8 is more consistent, clustering at **63.64–72.73%**, but three Claude artifacts also carry a separate proxy-validation exception. GPT-5.6-sol has one partial deployment at **63.64%** and three **9.09%** runs dominated by deployment prerequisites or path handling. All three downloaded Oracle attempts are platform/runtime startup failures and therefore have no score; the successful local Oracle baseline is **100% (11/11)**.
