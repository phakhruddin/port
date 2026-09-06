# Harbor Platform Mechanics

How a devcloud/Realm infrastructure task actually executes, based on tracing
the `signedgate-object-access` compose files and scripts. This is the
general mechanism — expect it to recur across other `networking-and-traffic`
style tasks on this platform.

## Two environments, one task

Every task ships **two** docker-compose stacks that look similar but serve
different phases:

| | `environment/docker-compose.yaml` | `tests/docker-compose.yaml` |
|---|---|---|
| Who runs it | The agent (solver) | The verifier (grader) |
| `main` service | Agent's working container; proxies all HTTP through a Daytona netleash sidecar (`HTTP_PROXY`, custom CA bundle) | Verifier container; runs pytest directly, no proxy |
| Networks | `agent` (external), `solver-control` (internal), `workload` (internal) | `verifier-control` (internal), `workload` (internal) — no external network at all |
| Config visibility | `/workspace/config:ro` — read-only | Same mount, plus a **second** read-only copy at `/workspace/runtime-config` as a fallback |

Both stacks share the same `runtime-setup` + `floci` service shapes. This
split matters: **the agent's image is not the verifier's image.** A
submission that only works because a tool is present in the agent
environment (e.g. `awscli`) can fail in the verifier if the two Dockerfiles
diverge — see `scoring-and-gotchas.md`.

## `runtime-setup`: where the task's runtime identity comes from

A short-lived container with the host Docker socket mounted. It:

1. Builds the supplied application image (`docker build -t <api>:<tag> /application`) — the agent/verifier never write or receive this image via a registry pull; it's built locally each run.
2. Generates a random `resource_prefix` (`sg-<12 hex chars>` for this task).
3. Computes the image's content digest (`docker image inspect --format '{{.Id}}'`) as `api_image_id` — this is why tasks require reading the image identity dynamically rather than hardcoding a tag.
4. Writes `/config/config.json` (mode `0444` — read-only even to its own writer after the move) and mirrors it to a backup path.
5. `chown`s the submission volume to the unprivileged UID the `main` container runs as (`10001:10001`).

This is the mechanism behind the task rule *"read config dynamically, never
copy values into source"* — the prefix and image digest are freshly
generated per run and would be wrong (or stale) if hardcoded.

## Floci: the AWS emulator

`mirror.gcr.io/floci/floci` — an AWS-API-compatible emulator, addressed as
`aws` / `000000000000.aws` on both the control and `workload` networks. Two
details change its behavior significantly from a "just mocks the API"
emulator:

- **`FLOCI_SERVICES_ECS_MOCK: "false"`** — ECS tasks are not simulated state;
  Floci actually launches Docker containers for them on the `workload`
  network. `assign_public_ip`, security groups, and container health checks
  have real effect.
- **`FLOCI_STORAGE_MODE: persistent`** — state survives container restarts
  within a run, backed by a named volume (`floci-data`).

Because it's a real (if imperfect) implementation rather than a pure mock,
it has its own emulation gaps and read-back quirks that a submission's
Terraform has to tolerate — documented in `scoring-and-gotchas.md`.

## The verifier runs a *copy*, not the original

`tests/suite/conftest.py` copies `/workspace/submission` (host-owned,
read-only in Harbor's model) to a writable `/tmp/signedgate-submission`
before running anything. Consequences:

- Any path derived from the submission's own location
  (`$(dirname "$0")/../config/config.json`, etc.) resolves differently after
  the copy and will fail. The only safe reference is the fixed absolute path
  handed to both agent and verifier (`/workspace/config/config.json` for
  this task).
- A `preflight.py` step runs *before* any cloud deployment specifically to
  reject this class of mistake cheaply — it greps `deploy.sh`/`destroy.sh`/
  `infra/*.tf` for any `config/config.json` reference and fails fast if one
  isn't the exact required absolute path.

## Grading loop

The verifier is a single pytest session against one shared, session-scoped
`deployment` fixture: it runs `deploy.sh` once, parses `manifest.json`, and
every test function depends on that fixture (directly, or via the
`credentials` fixture that requests OAuth tokens from the manifest's
`token_url`). This has a structural consequence worth internalizing: **if
the deployment fixture fails, every dependent test errors, not fails** — one
root cause can look like ten independent defects in the score. See
`scoring-and-gotchas.md` for how that interacts with the scoring formula.

`pytest_sessionfinish` in `conftest.py` writes the final
`{"reward": ..., "score": ...}` to `/logs/verifier/score.json` — this is the
file Harbor actually reads to grade the run.
