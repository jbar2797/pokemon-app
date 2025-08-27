# Release Policy (Freeze Until MVP)

**Policy:** No GitHub Releases will be created until the MVP milestone is approved.

- Git tags (e.g., sprint tags) may still be created for traceability.
- The `Release Freeze` workflow deletes any GitHub Release created during the freeze.
- When MVP is approved:
  - Create `v1.0.0` (or agreed SemVer) as the first Release.
  - From that point, Releases resume per the versioning policy.

**How to lift the freeze:**
- Remove or disable `.github/workflows/release-freeze.yml`.
- Re-enable any Release/Publish workflows as needed.
