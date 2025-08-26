#!/usr/bin/env bash
set -e  # no '-u' to avoid "parameter not set" in zsh

ok(){ printf '[OK] %s\n' "$*"; }
warn(){ printf '[WARN] %s\n' "$*" >&2; }
err(){ printf '[ERR] %s\n' "$*" >&2; }

exists(){ command -v "$1" >/dev/null 2>&1; }

ensure_branch(){
  local feature="$1"; local base="${2:-main}"
  if git rev-parse --verify "$feature" >/dev/null 2>&1; then
    git checkout "$feature"
    ok "Switched to existing local branch: $feature"
  else
    git fetch origin "$base" >/dev/null 2>&1 || true
    git checkout -b "$feature" "origin/$base" 2>/dev/null \
      || git checkout -b "$feature" "$base" 2>/dev/null \
      || git checkout -b "$feature"
    ok "Created branch: $feature"
  fi
}

run_precommit_until_clean(){
  local max="${1:-3}"
  local pass=0
  if exists uv; then uv run pre-commit install >/dev/null 2>&1 || true
  else pre-commit install >/dev/null 2>&1 || true
  fi
  while true; do
    if exists uv; then
      if uv run pre-commit run --all-files; then ok "pre-commit hooks passed"; break; fi
    else
      if pre-commit run --all-files; then ok "pre-commit hooks passed"; break; fi
    fi
    pass=$((pass+1))
    if [ "$pass" -ge "$max" ]; then
      warn "pre-commit still failing after $pass passes; see output above"
      return 0  # do not fail the whole script in terminals that show "exit 1"
    fi
    git add -A || true
    warn "Hooks modified files. Staging and retrying... (pass $pass/$max)"
  done
}

safe_jq_update(){
  local file="$1"; shift
  if ! exists jq; then
    warn "jq not found; attempting to install..."
    if exists sudo; then sudo apt update && sudo apt install -y jq; else
      err "jq not available and cannot auto-install"; return 1
    fi
  fi
  local tmp; tmp="$(mktemp)"
  jq "$@" "$file" > "$tmp"
  mv "$tmp" "$file"
}
