#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
infra_dir="$script_dir/infra"
config_file="/workspace/config/config.json"
manifest="$script_dir/manifest.json"

for command in terraform jq curl; do
  command -v "$command" >/dev/null || { echo "missing required command: $command" >&2; exit 2; }
done
[[ -r "$config_file" ]] || { echo "missing $config_file" >&2; exit 2; }
: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required}"

jq -e '
  (.resource_prefix | type == "string" and length >= 3) and
  (.region | type == "string" and length > 0) and
  (.aws_endpoint_url | test("^https?://[^/]+$")) and
  (.api_image | type == "string" and length > 0) and
  (.api_image_id | type == "string" and length > 0) and
  (.presign_ttl_seconds | type == "number" and . > 0 and . <= 300)
' "$config_file" >/dev/null

export TF_IN_AUTOMATION=1 TF_INPUT=0
export TF_VAR_aws_access_key_id="$AWS_ACCESS_KEY_ID"
export TF_VAR_aws_secret_access_key="$AWS_SECRET_ACCESS_KEY"
umask 077
jq '{prefix:.resource_prefix,aws_region:.region,aws_endpoint_url,api_image,api_image_id,presign_ttl_seconds}' \
  "$config_file" >"$infra_dir/config.auto.tfvars.json"

terraform -chdir="$infra_dir" init -input=false -no-color
terraform -chdir="$infra_dir" apply -input=false -auto-approve -lock-timeout=60s -no-color
terraform -chdir="$infra_dir" output -json manifest | jq . >"$manifest.tmp"
mv "$manifest.tmp" "$manifest"
chmod 0644 "$manifest"

url="$(jq -er .alb.connect_url "$manifest")"
deadline=$((SECONDS + 180))
ready_streak=0
while (( ready_streak < 6 )); do
  if curl -fsS --max-time 3 "$url/health/ready" >/dev/null 2>&1; then
    ((ready_streak += 1))
  else
    ready_streak=0
  fi
  (( SECONDS < deadline )) || { echo "SignedGate did not become ready" >&2; exit 1; }
  sleep 1
done
echo "SignedGate is ready: $url"
