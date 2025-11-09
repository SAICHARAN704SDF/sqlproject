#!/usr/bin/env bash
set -euo pipefail

# push_to_github.sh
# Usage:
#   ./push_to_github.sh <repo-name> [public|private] [github-username]
# Examples:
#   ./push_to_github.sh escape-stress public
#   ./push_to_github.sh escape-stress private myuser

REPO_NAME="${1:-escape-stress}"
VISIBILITY="${2:-public}"
GITHUB_USER="${3:-}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI 'gh' is not installed or not on PATH."
  echo "Install it from https://cli.github.com/ and run 'gh auth login' to authenticate."
  exit 1
fi

# Ensure we're at the repo root (where this script is located)
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

if [ ! -d .git ]; then
  echo "Initializing git repository..."
  git init
  git add .
  git commit -m "chore: initial commit"
else
  echo ".git already exists — will add and commit any uncommitted changes."
  git add .
  git commit -m "chore: update files" || true
fi

if [ -n "$GITHUB_USER" ]; then
  REPO_ARG="$GITHUB_USER/$REPO_NAME"
else
  REPO_ARG="$REPO_NAME"
fi

echo "Creating repository on GitHub: $REPO_ARG (visibility: $VISIBILITY)"
# create repo and push local contents; --source and --push will set remote and push
gh repo create "$REPO_ARG" --$VISIBILITY --source=. --remote=origin --push

echo "Repository created and pushed. Remote 'origin' is set to:"
git remote -v

echo "Done."
