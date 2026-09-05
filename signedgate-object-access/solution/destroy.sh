#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_dir="$script_dir/infra"
state="$infra_dir/terraform.tfstate"
[[ -f "$state" ]] || { echo "No SignedGate state; nothing to destroy."; exit 0; }
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"
export TF_IN_AUTOMATION=1 TF_INPUT=0
export TF_VAR_aws_access_key_id="$AWS_ACCESS_KEY_ID"
export TF_VAR_aws_secret_access_key="$AWS_SECRET_ACCESS_KEY"
[[ -d "$infra_dir/.terraform" ]] || terraform -chdir="$infra_dir" init -input=false -no-color
terraform -chdir="$infra_dir" destroy -input=false -auto-approve -lock-timeout=60s -no-color
[[ -z "$(terraform -chdir="$infra_dir" state list 2>/dev/null)" ]] || { echo "resources remain in state" >&2; exit 1; }
echo "SignedGate resources destroyed."
