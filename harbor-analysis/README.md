# Harbor Analysis

Internal analysis notes on the **Harbor** benchmark platform — the harness
that runs devcloud/Realm agent benchmark tasks against a Floci-emulated AWS
environment. This directory is independent of `fromdevcloud/`: it holds our
own derived analysis, not synced upstream content.

## Layout

```text
harbor-analysis/
├── README.md                          — this file
├── platform/
│   ├── mechanics.md                   — how Harbor + Floci actually run a task
│   └── scoring-and-gotchas.md         — scoring mechanics and known platform quirks
└── cases/
    └── signedgate-object-access/      — first case study
        ├── task-overview.md           — task spec, required graph, scoring rubric
        ├── reference-solution.md      — Oracle (golden) solution walkthrough
        └── model-run-comparison.md    — cross-model performance and failure patterns
```

`platform/` holds knowledge that should generalize across any devcloud/Harbor
task (compose topology, Floci behavior, scoring mechanics, environment-parity
pitfalls). `cases/<task-name>/` holds task-specific analysis. When we look at
a new infrastructure scenario, add a sibling under `cases/` rather than
overloading this one.

## Source material

This analysis was derived from `fromdevcloud/signedgate-object-access/` in
this repository (itself synced from `phakhruddin/mcr1:devcloud/signedgate-object-access`),
specifically:

- `task.toml`, `instruction.md`, `reasoning.md` — task definition and scoring intent
- `environment/workspace/contracts/**` — architecture, runtime, API and per-service contracts
- `environment/docker-compose.yaml`, `tests/docker-compose.yaml`, `tests/runtime/Dockerfile` — Harbor/Floci topology
- `solution/**` — the Oracle (golden) Terraform solution
- `tests/suite/**` — the actual pytest verifier suite
- `realm_run/**` — cross-model run comparisons (Claude Opus 4.8, Gemini 3.7 Flash, GPT-5.6-sol vs. Oracle)

Nothing here should be treated as authoritative task content — for the
canonical contracts and verifier, always read `fromdevcloud/signedgate-object-access/`
directly. This is our commentary layer on top of it.
