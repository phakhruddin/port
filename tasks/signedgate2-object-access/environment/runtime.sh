#!/bin/sh
set -eu

config_dir="${CONFIG_DIR:-/config}"
mkdir -p "$config_dir"
docker build -t signedgate/api:1.0.0 /application

resource_prefix="sg2-$(od -An -N6 -tx1 /dev/urandom | tr -d ' \n')"
image_id="$(docker image inspect --format '{{.Id}}' signedgate/api:1.0.0)"

config_tmp="$config_dir/config.json.tmp"
cat >"$config_tmp" <<EOF
{
  "resource_prefix": "$resource_prefix",
  "region": "us-east-1",
  "aws_endpoint_url": "http://aws:4566",
  "api_image": "signedgate/api:1.0.0",
  "api_image_id": "$image_id",
  "presign_ttl_seconds": 120
}
EOF
chmod 0444 "$config_tmp"
mv "$config_tmp" "$config_dir/config.json"
echo "SignedGate runtime configuration is ready."
