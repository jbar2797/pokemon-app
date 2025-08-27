# Release Policy (MVP Freeze)

**Policy:** We do **not** publish GitHub Releases or version tags (e.g., `v0.2.1`) until the initial MVP is approved.

## Why
- Prevents confusion around pre‑MVP artifacts.
- Keeps users focused on the live MVP milestone rather than pre‑releases.

## How We Enforce It
- **Actions:** `.github/workflows/release-freeze.yml` is enabled. If a Release is created, the workflow deletes it.
- **Publishers:** Any “Release/Publish” workflow is disabled.
- **Helper:** `scripts/enforce_release_freeze.sh` keeps the policy enforced.

## Lifting the Freeze
1. Re‑enable the Release workflow(s):
   `gh workflow enable .github/workflows/release.yml`
2. Disable the freeze guard (optional once we’re truly ready):
   `gh workflow disable .github/workflows/release-freeze.yml`
3. Tag and publish the first MVP Release (e.g., `v1.0.0`).
