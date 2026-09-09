# SignedGate2 Object Access

You're building the infrastructure for **SignedGate**, a private file
exchange that hands out short-lived, single-purpose S3 presigned URLs
instead of proxying file bytes itself. The API (already written, you don't
touch it) authenticates the caller, checks role/ownership rules, and
either returns a presigned URL or a 403. Everything after that, the
actual `GET`/`PUT`/`DELETE`, happens directly between the client and S3.
The API container never sees the file bytes, and it shouldn't.

This is a networking task at heart: put the ALB on the internet, keep
everything else off it, and give the API a private path to S3 through a
gateway VPC endpoint rather than routing object traffic out to the public
internet and back.

> **Solved v1 before?** Read "What changed from v1" at the bottom first.
> A few things below are new or spelled out more precisely because the
> last version, both the task text and the verifier, had some real gaps
> that cost people points for reasons that had nothing to do with their
> RBAC logic.

## Roles

| Role | Create | Read | Update | Delete |
|---|---:|---:|---:|---:|
| `viewer` | no | shared objects | no | no |
| `contributor` | yes | owned or shared objects | owned objects | owned objects |
| `admin` | yes | all objects | all objects | all objects |

The API image is supplied, so don't replace it, and don't put anything in
front of it that proxies file content. Every presigned URL you hand out
has to be scoped to one HTTP method, one object key, and at most 300
seconds of validity.

## Read the contracts first

Before you write any Terraform, go read `/workspace/contracts/`:

- `architecture.md`: the resource graph you're expected to build
- `runtime.md`: the supplied image and what env vars it needs
- `openapi.yaml`: the API surface and what each call is supposed to do
- `services/*.md`: the fine print per AWS service (network, identity, storage, compute, observability)
- `schemas/manifest.schema.json`: the shape of the manifest your `deploy.sh` has to produce

`/workspace/config/config.json` is generated fresh for every run: resource
prefix, region, endpoint URL, the image digest, all of it. Read it at
deploy time, every time. Don't hardcode any of it into your Terraform or
scripts; it'll be different next run and your submission will break.

One thing that trips people up: the verifier doesn't run your submission
in place. It copies `/workspace/submission` somewhere else first and runs
it from there. So any path you build relative to your own script's
location (`$(dirname "$0")/../config/config.json`, that kind of thing)
will resolve to the wrong place after the copy. Always reference the
config by its fixed absolute path, `/workspace/config/config.json`. There's
no working around this one, it's baked into how the grading environment
works.

You can drop diagnostics under `/workspace/evidence/` if that's useful to
you. Just don't touch the contracts, the config, or the supplied image;
none of that is yours to change.

## What you actually have to hand back

```text
/workspace/submission/
├── deploy.sh
├── destroy.sh
├── manifest.json       # deploy.sh writes this
└── infra/
    └── one or more *.tf files
```

A few things worth calling out beyond "make it work":

- `deploy.sh` needs to init/apply your Terraform (or OpenTofu), write out a
  manifest that matches the schema, and actually wait until the service is
  healthy before exiting. Don't just fire `terraform apply` and declare
  victory.
- Everything has to keep working after the submission directory gets
  copied elsewhere, for the reason above. Don't build in any assumption
  about where `deploy.sh` itself lives.
- **Persist your dynamic Terraform inputs to an auto-loaded var file**,
  something like `infra/config.auto.tfvars.json`, written by `deploy.sh`
  before you `init`/`apply`. Here's why this matters more than it sounds
  like it should. The verifier runs `terraform plan` directly against
  `infra/`, without going through your `deploy.sh` at all, to check the
  deployment is stable. If the only place a required variable ever gets a
  value is a `-var` flag inside `deploy.sh`, that standalone plan has
  nothing to work with and just fails, even though your actual deployment
  was fine. We grade this as a real lifecycle bug on your end this time
  around, not a platform quirk, so don't leave it to chance.
- The manifest's `auth` block needs every client's ID and secret, using
  the exact field names the schema wants. The verifier uses these to pull
  role-scoped tokens for itself; get a field name wrong and every
  behavioral test fails at the token step, before it even gets to test
  anything interesting.
- The `alb` object needs two different things, and they are **not the
  same URL**:
  - `alb.dns_name` / `alb.url`: the real, provider-generated ALB
    hostname. Fine for observability, accurate is good, but nothing in
    this environment can actually resolve that hostname from outside the
    ALB's own path.
  - `alb.connect_url`: the URL the verifier is actually going to hit.
    This has to resolve from the verifier's container, which means the
    shared AWS-compatible endpoint (the host portion of `aws_endpoint_url`
    from your config, port 80), not the generated ALB DNS name. **Do not
    put the ALB's real DNS name here.** This is, by a wide margin, the
    single most common way a perfectly correct RBAC/CRUD implementation
    scores zero on every behavioral test: the request just never shows
    up, so there's nothing to grade.
- `deploy.sh` has to be safe to run more than once, and it needs to repair
  anything that got deleted out of your networking layer without touching
  the S3 bucket or the DynamoDB table.
- `destroy.sh` only removes what this deployment owns, including every
  version of every object in the bucket, not just the current one.
- Your `terraform.tfstate` needs to actually contain everything required.
  You can use the AWS CLI to poke around and check things, but not to
  stand up infrastructure that should have come from Terraform. And don't
  worry about whether it's there: the verifier's image ships with the
  same tools yours does (`bash`, `curl`, `jq`, `terraform`, `aws`), and we
  check that at image build time now, so you don't need to defensively
  code around a missing binary.

Budget: 720 seconds to deploy, 900 to destroy. Each script tops out at 8
MiB of output, and `manifest.json` can't exceed 1 MiB.

## What "done" actually looks like

1. At least two healthy API tasks, sitting behind one public ALB.
2. Those tasks live in private subnets, no public IPs.
3. S3 traffic from the private subnets goes out through a gateway VPC
   endpoint, not the public internet.
4. The bucket is private, versioned, and encrypted with a key you control.
5. Ownership/sharing metadata lives in an encrypted DynamoDB table.
6. RBAC actually holds for presigned `GET`/`PUT`/`DELETE`, and this
   includes a viewer **successfully reading** a file someone shared with
   them, not just getting turned away when they try to create one.
7. Unsigned requests, tampered signatures, cross-user access, and key
   traversal all get rejected.
8. Re-running `deploy.sh` after we delete a managed route, endpoint, or
   target attachment brings the topology back, and does *only* that. A
   standalone `terraform plan -refresh=false` afterward should show
   nothing pending, not even something harmless.
9. Logs carry request IDs and authorization decisions, and nothing else:
   no credentials, no bearer tokens, no client secrets, no full presigned
   URLs. We check this directly against the captured log stream, not by
   reading your code and trusting it.

## Scoring

This is different from v1: the score is **weighted by category** (table
below) and computed per category, not as one flat pass-count over every
test. Practically, this means if a shared setup failure wipes out every
test in one category, you lose that category's points and nothing else.
It doesn't quietly eat into unrelated categories the way a flat ratio
would. If you want to reason about partial credit, `architecture.md` shows
which test maps to which category.

| Category | Points |
|---|---:|
| RBAC and tenant isolation | 25 |
| Presigned CRUD behavior | 20 |
| Networking and traffic topology | 20 |
| Security and encryption | 15 |
| Recovery and stable redeployment | 12 |
| Observability and clean destruction | 8 |
| **Total** | **100** |

## What changed from v1

This is a straight revision of `signedgate-object-access`, driven by
actually looking at how prior runs failed. If v1 is fresh in your memory,
here's what's different and why it matters:

- **Scoring is per-category and weighted now**, not one flat pass/total
  ratio. A shared setup failure still zeroes out whatever depends on it,
  but it no longer drags down categories it has nothing to do with.
- **`alb.connect_url` is now spelled out explicitly**, and there's a fast
  connectivity check that runs before the behavioral suite. If you get
  this wrong, you'll get told exactly that, not three seemingly-unrelated
  RBAC failures that you'll waste an hour debugging in the wrong place.
- **Persisting Terraform inputs to an auto-loaded var file is now a named
  requirement**, not something you had to reverse-engineer from a cryptic
  `test_stable_redeployment` failure.
- **Viewer-reads-a-shared-file, signature tampering, and log hygiene are
  now actually tested.** In v1 you could pass the whole suite without
  ever demonstrating any of these, even though the task said they were
  required.
- **The verifier and the agent environment are now guaranteed to have the
  same tools.** We check this at image build time. If the contract says
  you can use it, it'll be there when the verifier relocates your
  submission; you shouldn't get burned by an environment mismatch that
  has nothing to do with your actual solution.
