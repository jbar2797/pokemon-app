#!/usr/bin/env bash
set -Eeuo pipefail

# Deletes all GitHub Releases for the current repo (leaves tags in place).
# Requires: gh CLI authenticated to the repo.

REPO_NWO="$(gh repo view --json nameWithOwner -q '.nameWithOwner')"
echo "Repository: ${REPO_NWO}"

# Pull all release tag names (JSON path is robust across gh versions that support --json)
mapfile -t RELEASE_TAGS < <(gh release list --repo "${REPO_NWO}" --limit 200 \
  --json tagName -q '.[].tagName' 2>/dev/null || true)

if [[ ${#RELEASE_TAGS[@]} -eq 0 ]]; then
  echo "No releases found. Nothing to delete."
  exit 0
fi

echo "Found ${#RELEASE_TAGS[@]} release(s): ${RELEASE_TAGS[*]}"
for tag in "${RELEASE_TAGS[@]}"; do
  echo "Deleting release for tag: ${tag}"
  gh release delete "${tag}" --repo "${REPO_NWO}" -y || true
done

echo "Done. Releases removed (tags untouched)."
