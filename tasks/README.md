# Tasks

Devcloud/Harbor-style benchmark tasks authored in this repository (as
opposed to `fromdevcloud/`, which holds content synced from the upstream
`devcloud` source repo, and `harbor-analysis/`, which holds our analysis of
that platform).

## signedgate2-object-access

A revision of `fromdevcloud/signedgate-object-access`, incorporating the
findings in `harbor-analysis/`: weighted category scoring, an explicit
`alb.connect_url` contract, enforced verifier/agent tool parity, Floci
emulation-gap hardening, and closed test-coverage gaps (viewer-can-read-shared,
signature tampering, log hygiene). See
`signedgate2-object-access/CHANGELOG.md` for the full list of changes and the
specific `harbor-analysis/` finding each one addresses.
