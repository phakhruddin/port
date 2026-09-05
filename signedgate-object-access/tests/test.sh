#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /logs/verifier
rm -f /logs/verifier/reward.json /logs/verifier/reward.txt /logs/verifier/report.json
export PYTHONPATH="/tests${PYTHONPATH:+:$PYTHONPATH}"

ensure_reward_file() {
  if [[ ! -s /logs/verifier/reward.json ]]; then
    printf 'verifier exited before scoring completed; emitting zero reward\n' >&2
    printf '{"reward":0,"score":0}\n' >/logs/verifier/reward.json
  fi
  if [[ ! -s /logs/verifier/reward.txt ]]; then
    jq -r '.reward' /logs/verifier/reward.json >/logs/verifier/reward.txt
  fi
}
trap ensure_reward_file EXIT

if ! python /tests/preflight.py; then
  # Harbor treats every top-level reward value as a numeric reward component.
  # Keep diagnostics in test stdout and emit numeric fields only here.
  printf '{"reward":0,"score":0}\n' >/logs/verifier/score.json
  cp /logs/verifier/score.json /logs/verifier/reward.json
  jq -r '.reward' /logs/verifier/reward.json >/logs/verifier/reward.txt
  cp /logs/verifier/reward.json /logs/verifier/report.json
  exit 1
fi

set +e
python -m pytest -q --tb=short /tests/suite
rc=$?
set -e

if [[ -s /logs/verifier/score.json ]]; then
  cp /logs/verifier/score.json /logs/verifier/reward.json
else
  printf '{"reward":0,"score":0}\n' >/logs/verifier/reward.json
fi
jq -r '.reward' /logs/verifier/reward.json >/logs/verifier/reward.txt
cp /logs/verifier/reward.json /logs/verifier/report.json
exit "$rc"
