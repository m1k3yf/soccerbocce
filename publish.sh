#!/usr/bin/env bash
# Publish SoccerBocce to GitHub Pages.
#
#   1) Create an empty repo named "soccerbocce" on github.com (no README).
#   2) Run:  bash publish.sh https://github.com/<you>/soccerbocce.git
#   3) On github.com: Settings → Pages → Deploy from branch → main / root.
#
# Re-running later just commits + pushes the latest build.
set -e

REMOTE="${1:-}"

if [ ! -d .git ]; then
  git init
  git branch -M main
fi

if [ -n "$REMOTE" ] && ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$REMOTE"
fi

git add -A
git commit -m "Publish SoccerBocce" || echo "Nothing new to commit."

if git remote get-url origin >/dev/null 2>&1; then
  git push -u origin main
  echo "Pushed. Enable Pages: Settings → Pages → main / root."
else
  echo "No 'origin' remote set. Re-run:  bash publish.sh <repo-url>"
fi
