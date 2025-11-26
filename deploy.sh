#!/bin/bash
# Deploy site to gh-pages branch

set -e

echo "Building site..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python generate_site.py
python generate_councilfile_pages.py

echo ""
echo "Deploying to gh-pages branch..."

# Store current branch
CURRENT_BRANCH=$(git branch --show-current)

# Create a temporary directory
TEMP_DIR=$(mktemp -d)

# Copy ONLY site files to temp
cp -r site/* "$TEMP_DIR/"

# Backup .env file if it exists
ENV_BACKUP=""
if [ -f ".env" ]; then
    ENV_BACKUP=$(mktemp)
    cp .env "$ENV_BACKUP"
    echo "Backed up .env file"
fi

# Now stash changes (the generated site files) so we can switch branches
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Stashing generated files..."
    git stash push -u -m "Auto-stash generated files before branch switch"
    STASHED=true
else
    STASHED=false
fi

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

# Remove any sensitive files that shouldn't be deployed (they survive branch switch since they're untracked)
# Note: .env is already backed up to $ENV_BACKUP and will be restored after switching back to master
rm -f .env .env.* *.key *.pem 2>/dev/null || true

# Add and commit
git add -A
git commit -m "Deploy site $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
echo "Pushing to GitHub..."
git push -f origin gh-pages

# Switch back to original branch
git checkout "$CURRENT_BRANCH"

# Restore stashed changes if any
if [ "$STASHED" = true ]; then
    echo "Restoring stashed changes..."
    git stash pop
fi

# Restore .env file if it was backed up
if [ -n "$ENV_BACKUP" ] && [ -f "$ENV_BACKUP" ]; then
    cp "$ENV_BACKUP" .env
    rm "$ENV_BACKUP"
    echo "Restored .env file"
fi

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
