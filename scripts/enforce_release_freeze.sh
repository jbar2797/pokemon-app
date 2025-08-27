#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "==> Enforce 'no Releases until MVP'"
# Disable any workflow that looks like a publisher
for wf in $(gh workflow list --json name,path -q '.[] | select(.name | test("(?i)release|publish")) | .path'); do
  if [[ "$wf" != ".github/workflows/release-freeze.yml" ]]; then
    echo "Disabling publisher workflow: $wf"
    gh workflow disable "$wf" || true
  fi
done

# Ensure the freeze guard is ON
echo "Enabling freeze guard: .github/workflows/release-freeze.yml"
gh workflow enable ".github/workflows/release-freeze.yml" || true

# Clean up any accidental Releases (keeps tags)
echo "Deleting any Releases (if present)..."
if gh release list -L 1 | grep -q .; then
  while read -r TAG _; do
    echo "Deleting release for tag: $TAG"
    gh release delete "$TAG" --yes || true
  done < <(gh release list | awk '{print $1}')
else
  echo "No Releases found."
fi

echo "Policy enforced."
