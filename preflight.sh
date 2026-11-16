#!/usr/bin/env bash
# preflight.sh — Sankofa Day 0 hygiene check
# Run from the root of a repo before starting any editing session:
#   bash preflight.sh
# Read-only: it reports problems, it never changes anything.

FAILS=0
WARNS=0
ok()   { printf "  [ok]   %s\n" "$1"; }
warn() { printf "  [warn] %s\n" "$1"; WARNS=$((WARNS+1)); }
fail() { printf "  [FAIL] %s\n" "$1"; FAILS=$((FAILS+1)); }

echo "== Git: source of truth =="
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  fail "not inside a git repo — run from the repo root"
  exit 1
fi
ROOT=$(git rev-parse --show-toplevel)
ok "repo: $ROOT"
BRANCH=$(git rev-parse --abbrev-ref HEAD)
ok "branch: $BRANCH"

if [ -n "$(git status --porcelain)" ]; then
  fail "uncommitted changes — commit or stash before editing anywhere else:"
  git status --short | sed 's/^/           /'
else
  ok "working tree clean"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git fetch origin --quiet 2>/dev/null || warn "could not fetch origin (offline or auth)"
  UP=$(git rev-parse --abbrev-ref '@{u}' 2>/dev/null)
  if [ -n "$UP" ]; then
    AHEAD=$(git rev-list --count "$UP"..HEAD)
    BEHIND=$(git rev-list --count HEAD.."$UP")
    [ "$AHEAD" -gt 0 ]  && fail "$AHEAD commit(s) not pushed — GitHub is behind your disk"
    [ "$BEHIND" -gt 0 ] && fail "$BEHIND commit(s) on remote you don't have — pull before editing"
    [ "$AHEAD" -eq 0 ] && [ "$BEHIND" -eq 0 ] && ok "in sync with $UP"
  else
    warn "branch has no upstream set"
  fi
else
  fail "no 'origin' remote configured"
fi

echo "== Secrets hygiene =="
if [ -f .gitignore ] && grep -qE '^\.env$' .gitignore; then ok ".env is in .gitignore"; else fail ".env missing from .gitignore"; fi
if [ -f .gitignore ] && grep -qE '^__pycache__/?$' .gitignore; then ok "__pycache__ is in .gitignore"; else warn "__pycache__ not in .gitignore"; fi
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  fail ".env is TRACKED by git — remove with 'git rm --cached .env' and rotate the key"
else
  ok ".env is not tracked"
fi
if [ -f .env ] && grep -qE '^ANTHROPIC_API_KEY=.+' .env; then
  ok "ANTHROPIC_API_KEY present in .env (value not shown)"
else
  warn "no ANTHROPIC_API_KEY in ./.env"
fi

echo "== Python environment =="
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)
if [ -z "$PYV" ]; then
  fail "python3 not found"
else
  python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)' && ok "python $PYV" || fail "python $PYV — need 3.11+"
fi
[ -n "$VIRTUAL_ENV" ] && ok "venv active: $VIRTUAL_ENV" || warn "no venv active"
python3 -c 'import anthropic' 2>/dev/null && ok "anthropic SDK importable" || fail "anthropic SDK not importable in this interpreter"
python3 -c 'import dotenv' 2>/dev/null && ok "python-dotenv importable" || fail "python-dotenv not importable"

echo "== Split-brain check: duplicate copies of tracked files =="
# Finds same-named files outside this repo whose contents differ from the tracked copy.
SEARCH_DIRS="$HOME/Downloads $HOME/Desktop $HOME/Documents $HOME/dev"
DUPES=0
while IFS= read -r f; do
  base=$(basename "$f")
  for d in $SEARCH_DIRS; do
    [ -d "$d" ] || continue
    while IFS= read -r other; do
      case "$other" in "$ROOT"/*) continue;; esac
      if ! cmp -s "$ROOT/$f" "$other"; then
        warn "differing copy: $other"
        DUPES=$((DUPES+1))
      fi
    done < <(find "$d" -maxdepth 4 -type f -name "$base" 2>/dev/null)
  done
done < <(git ls-files | grep -E '\.(html|py|sh)$')
[ "$DUPES" -eq 0 ] && ok "no diverging copies found"

echo
echo "Result: $FAILS fail, $WARNS warn"
[ "$FAILS" -eq 0 ] && echo "Clear to edit." || echo "Resolve FAILs before editing."
exit "$FAILS"
