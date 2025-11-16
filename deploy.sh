#!/bin/bash
# Deploy site to gh-pages branch

set -e

echo "Building site..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python generate_site.py

echo ""
echo "Deploying to gh-pages branch..."

# Store current branch
CURRENT_BRANCH=$(git branch --show-current)

# Create a temporary directory
TEMP_DIR=$(mktemp -d)

# Copy ONLY site files to temp
cp -r site/* "$TEMP_DIR/"

# Switch to gh-pages branch (create if doesn't exist)
if git show-ref --verify --quiet refs/heads/gh-pages; then
    git checkout gh-pages
    # Clean existing files
    git rm -rf .
else
    git checkout --orphan gh-pages
    # Remove all files from index
    git rm -rf .
fi

# Copy files from temp to root (flatten the directory structure)
cp -r "$TEMP_DIR"/* .

# Clean up temp
rm -rf "$TEMP_DIR"

# Add and commit
git add -A
git commit -m "Deploy site $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
echo "Pushing to GitHub..."
git push -f origin gh-pages

# Switch back to original branch
git checkout "$CURRENT_BRANCH"

echo ""
echo "✅ Deployed to gh-pages branch!"
echo ""
echo "Next steps:"
echo "1. Go to: https://github.com/$(git config remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/settings/pages"
echo "2. Set Source to: Deploy from branch"
echo "3. Set Branch to: gh-pages"
echo "4. Set Folder to: / (root)"
echo "5. Save"
echo ""
echo "Your site will be available at:"
echo "https://$(git config remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/' | cut -d'/' -f1).github.io/$(git config remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/' | cut -d'/' -f2)"
