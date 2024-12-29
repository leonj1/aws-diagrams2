#!/bin/bash

# Create symlink from .git/hooks/pre-commit to .githooks/pre-commit
echo "Setting up Git hooks..."

# Remove existing pre-commit hook if it exists
if [ -f .git/hooks/pre-commit ]; then
    rm .git/hooks/pre-commit
fi

# Create symlink
ln -s ../../.githooks/pre-commit .git/hooks/pre-commit

# Make sure the hook is executable
chmod +x .githooks/pre-commit

echo "✅ Git hooks setup complete!"
