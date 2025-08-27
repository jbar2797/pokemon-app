#!/usr/bin/env bash
set -Eeuo pipefail

# Requires: GitHub CLI authenticated with repo admin rights.
# Protects the 'main' branch: PRs required + CI check required.

OWNER_REPO="$(git remote get-url origin | sed -E 's#.*github\.com[:/](.+)\.git#\1#')"
BRANCH="main"

# This must match the name of your required status check.
# If your workflow is named differently, update the string below.
REQUIRED_CHECK="CI - Tests & Coverage"

echo "Protecting ${OWNER_REPO}:${BRANCH} (require PR + status checks)…"

gh api \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  "repos/${OWNER_REPO}/branches/${BRANCH}/protection" \
  -f required_status_checks.strict=true \
  -f required_status_checks.contexts[]="${REQUIRED_CHECK}" \
  -f enforce_admins=true \
  -F restrictions= \
  -f required_pull_request_reviews.dismiss_stale_reviews=true \
  -f required_pull_request_reviews.required_approving_review_count=1 \
  -f required_linear_history=true \
  -f allow_force_pushes=false \
  -f allow_deletions=false

echo "Branch protection applied to ${OWNER_REPO}:${BRANCH}."
