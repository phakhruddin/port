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

# v2 addition: catch the single most common lifecycle defect from v1 before
# any cloud spend happens. The verifier runs `terraform plan` directly
# against infra/, without going through deploy.sh (see
# tests/suite/test_lifecycle.py::test_stable_redeployment). A deploy.sh that
# only ever passes dynamic values via `-var`/`-var-file` flags on `apply`
# will pass deployment and then fail that standalone plan later, which is a
# much more confusing place to discover this. Flag it here instead, cheaply.
deploy_sh = submission / "deploy.sh"
deploy_text = deploy_sh.read_text(errors="replace") if deploy_sh.is_file() else ""
persists_tfvars = bool(re.search(r"\.auto\.tfvars(\.json)?", deploy_text)) or bool(
    re.search(r"-var-file", deploy_text)
)
if not persists_tfvars:
    print(
        "submission preflight failed: deploy.sh does not appear to persist "
        "dynamic Terraform inputs to an auto-loaded variable file (for "
        "example infra/config.auto.tfvars.json). The verifier runs "
        "`terraform plan` directly against infra/ without invoking "
        "deploy.sh; variables only passed via `-var` flags to `apply` will "
        "be undefined for that standalone plan. See "
        "contracts/architecture.md's \"Shared rules\".",
        file=sys.stderr,
    )
    raise SystemExit(1)
