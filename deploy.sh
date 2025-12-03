#!/bin/bash
# Deploy site to gh-pages branch
#
# This script:
# 1. Fetches latest meetings (ensures recent_meetings.json exists)
# 2. Generates the site
# 3. Copies site/ to gh-pages branch and pushes

set -e

echo "Building site..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Step 1: Ensure we have meeting data (this creates recent_meetings.json)
if [ ! -f "recent_meetings.json" ]; then
    echo "Fetching meeting data..."
    python fetch_meetings.py
fi

# Step 2: Generate site (needs recent_meetings.json for committee data)
python generate_site.py
python aggregate_council_files.py
python generate_councilfile_pages.py

echo ""
echo "Deploying to gh-pages branch..."

# Store current branch
CURRENT_BRANCH=$(git branch --show-current)

# Create a temporary directory and copy site files
TEMP_DIR=$(mktemp -d)
cp -r site/* "$TEMP_DIR/"

# Use git worktree for clean branch switching (no stash needed)
WORKTREE_DIR=$(mktemp -d)

# Check if gh-pages exists remotely or locally
if git show-ref --verify --quiet refs/heads/gh-pages; then
    git worktree add "$WORKTREE_DIR" gh-pages
else
    # Create orphan gh-pages branch in worktree
    git worktree add --detach "$WORKTREE_DIR"
    cd "$WORKTREE_DIR"
    git checkout --orphan gh-pages
    git rm -rf . 2>/dev/null || true
    cd - > /dev/null
fi

# Copy site files to worktree
rm -rf "$WORKTREE_DIR"/* 2>/dev/null || true
cp -r "$TEMP_DIR"/* "$WORKTREE_DIR/"

# Commit and push from worktree
cd "$WORKTREE_DIR"
git add -A
git commit -m "Deploy site $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"
git push -f origin gh-pages
cd - > /dev/null

# Clean up
rm -rf "$TEMP_DIR"
git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || rm -rf "$WORKTREE_DIR"

echo ""
echo "✅ Deployed to gh-pages branch!"
echo ""
echo "Your site is available at: https://councilreader.com"
