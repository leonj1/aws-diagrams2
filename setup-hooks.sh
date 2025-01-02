#!/bin/bash

echo "Setting up Git hooks..."

# Remove existing pre-push hook if it exists
if [ -f .git/hooks/pre-push ]; then
    rm .git/hooks/pre-push
fi

# Copy pre-push hook
cp .githooks/pre-push .git/hooks/pre-push

# Make sure the hook is executable
chmod +x .git/hooks/pre-push

echo "✅ Git hooks setup complete!"
