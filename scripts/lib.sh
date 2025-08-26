#!/usr/bin/env bash
# NOTE: Do NOT set -u here; this file is sourced into interactive shells.

# --- tiny log helpers ---------------------------------------------------------
msg()  { printf '%s\n'    "$*"; }
ok()   { printf '[OK] %s\n'   "$*"; }
warn() { printf '[WARN] %s\n' "$*" >&2; }
err()  { printf '[ERR] %s\n'  "$*" >&2; }

# --- existence check ----------------------------------------------------------
exists() { command -v "$1" >/dev/null 2>&1; }

# --- pre-commit wrapper (prefers uv) -----------------------------------------
pc() {
  if exists uv; then
    uv run pre-commit "$@"
  elif exists pre-commit; then
    pre-commit "$@"
  else
    warn "pre-commit not available; skipping hook step: $*"
    return 0
  fi
}

# --- run hooks until clean (idempotent) --------------------------------------
run_precommit_until_clean() {
  # usage: run_precommit_until_clean [max_passes]
  local max="${1:-3}"
  local pass=0
  pc install >/dev/null 2>&1 || true
  while true; do
    if pc run --all-files; then
      ok "pre-commit hooks passed"
      break
    fi
    pass=$((pass+1))
    if [ "$pass" -ge "$max" ]; then
      warn "pre-commit still failing after $pass passes; see output above"
      break
    fi
    git add -A || true
    warn "Hooks modified files. Staging and retrying... (pass $pass/$max)"
  done
}

# --- branch helper (idempotent) ----------------------------------------------
ensure_branch() {
  # usage: ensure_branch <feature_branch> [base_branch]
  local feature="$1"
  local base="${2:-main}"

  git fetch origin "$base" >/dev/null 2>&1 || true
  if git rev-parse --verify "$feature" >/dev/null 2>&1; then
    git checkout "$feature"
    ok "Switched to existing local branch: $feature"
  else
    git checkout -b "$feature" "origin/$base" 2>/dev/null \
    || git checkout -b "$feature" "$base" 2>/dev/null \
    || git checkout -b "$feature"
    ok "Created branch: $feature"
  fi
}

# --- jq safe updater ----------------------------------------------------------
safe_jq_update() {
  # usage: safe_jq_update <file> <jq-filter...>
  local file="$1"; shift
  if ! exists jq; then
    warn "jq not found; attempting to install (Ubuntu)..."
    if exists sudo; then
      sudo apt update && sudo apt install -y jq
    else
      err "Cannot install jq automatically; please install jq and re-run."
      return 1
    fi
  fi
  local tmp; tmp="$(mktemp)"
  jq "$@" "$file" > "$tmp"
  mv "$tmp" "$file"
}
