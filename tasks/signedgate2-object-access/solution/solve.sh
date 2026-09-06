#!/usr/bin/env bash
set -Eeuo pipefail

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target_dir="/workspace/submission"
mkdir -p "$target_dir/infra"
cp "$source_dir/deploy.sh" "$source_dir/destroy.sh" "$target_dir/"
cp "$source_dir/infra/"*.tf "$target_dir/infra/"
chmod +x "$target_dir/deploy.sh" "$target_dir/destroy.sh"
exec "$target_dir/deploy.sh"
