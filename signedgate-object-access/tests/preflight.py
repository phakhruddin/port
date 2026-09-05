#!/usr/bin/env python3
"""Cheap submission checks that should fail before cloud deployment starts."""

import os
import re
import sys
from pathlib import Path


submission = Path(os.getenv("SIGNEDGATE_SUBMISSION_DIR", "/workspace/submission"))
candidate_files = [submission / "deploy.sh", submission / "destroy.sh"]
candidate_files.extend(sorted((submission / "infra").glob("*.tf")))

missing = [str(path.relative_to(submission)) for path in candidate_files[:2] if not path.is_file()]
if missing:
    print(f"submission preflight failed: missing required file(s): {', '.join(missing)}", file=sys.stderr)
    raise SystemExit(1)

references = []
for path in candidate_files:
    if not path.is_file():
        continue
    for line_number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if "config/config.json" in line:
            references.append((path, line_number, line.strip()))

if not references:
    print(
        "submission preflight failed: deploy scripts or Terraform must read "
        "/workspace/config/config.json dynamically",
        file=sys.stderr,
    )
    raise SystemExit(1)

invalid = []
for path, line_number, line in references:
    normalized = re.sub(r"[\\\"']", "", line)
    if "/workspace/config/config.json" not in normalized:
        invalid.append(f"{path.relative_to(submission)}:{line_number}: {line}")

if invalid:
    print(
        "submission preflight failed: runtime configuration references must use "
        "the absolute path /workspace/config/config.json because the verifier "
        "relocates the submission",
        file=sys.stderr,
    )
    for item in invalid:
        print(f"  {item}", file=sys.stderr)
    raise SystemExit(1)
