#!/bin/bash

# GitHub Secrets Setup Script
# This script helps you set up GitHub Actions secrets for Digital Ocean deployment

set -e

echo "🔐 GitHub Secrets Setup for Digital Ocean Deployment"
echo ""

# Configuration
DO_HOST="${DO_HOST:-159.65.18.16}"
DO_USER="${DO_USER:-root}"
SSH_KEY_PATH="${HOME}/.ssh/do_deploy"
REPO_NAME="seb-thomas/scaling-engine"

# Check if GitHub CLI is installed
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI (gh) detected"
    USE_GH_CLI=true
else
    echo "⚠️  GitHub CLI not found - will provide manual instructions"
    USE_GH_CLI=false
fi

# Step 1: Generate SSH key if it doesn't exist
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo ""
    echo "📝 Generating SSH key for deployment..."
    ssh-keygen -t ed25519 -C "github-actions-deploy" -f "$SSH_KEY_PATH" -N "" -q
    echo "✅ SSH key generated at: $SSH_KEY_PATH"
else
    echo ""
    echo "✅ SSH key already exists at: $SSH_KEY_PATH"
fi

# Step 2: Copy public key to Digital Ocean droplet
echo ""
echo "📤 Copying public key to Digital Ocean droplet..."
echo "   (You may be prompted for your droplet password)"

if ssh-copy-id -i "${SSH_KEY_PATH}.pub" -o StrictHostKeyChecking=no "${DO_USER}@${DO_HOST}" 2>/dev/null; then
    echo "✅ Public key copied successfully"
else
    echo "⚠️  Could not automatically copy key. Please run manually:"
    echo "   ssh-copy-id -i ${SSH_KEY_PATH}.pub ${DO_USER}@${DO_HOST}"
    echo ""
    read -p "Press Enter after you've copied the key manually..."
fi

# Step 3: Test SSH connection
echo ""
echo "🔍 Testing SSH connection..."
if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "${DO_USER}@${DO_HOST}" "echo 'Connection successful'" 2>/dev/null; then
    echo "✅ SSH connection test passed"
else
    echo "⚠️  SSH connection test failed. Please verify:"
    echo "   1. The droplet is accessible"
    echo "   2. The public key was copied correctly"
    echo "   3. You can connect manually: ssh -i $SSH_KEY_PATH ${DO_USER}@${DO_HOST}"
    exit 1
fi

# Step 4: Add secrets to GitHub
echo ""
echo "🔑 Adding secrets to GitHub..."

if [ "$USE_GH_CLI" = true ]; then
    # Check if user is logged in
    if ! gh auth status &>/dev/null; then
        echo "⚠️  Not logged into GitHub CLI. Please run: gh auth login"
        USE_GH_CLI=false
    fi
fi

if [ "$USE_GH_CLI" = true ]; then
    echo "   Using GitHub CLI to add secrets..."
    
    # Add DO_HOST
    echo "$DO_HOST" | gh secret set DO_HOST --repo "$REPO_NAME"
    echo "   ✅ DO_HOST added"
    
    # Add DO_USER
    echo "$DO_USER" | gh secret set DO_USER --repo "$REPO_NAME"
    echo "   ✅ DO_USER added"
    
    # Add DO_SSH_KEY
    cat "$SSH_KEY_PATH" | gh secret set DO_SSH_KEY --repo "$REPO_NAME"
    echo "   ✅ DO_SSH_KEY added"
    
    echo ""
    echo "✅ All secrets added successfully via GitHub CLI!"
else
    echo ""
    echo "📋 Manual Setup Required:"
    echo ""
    echo "Go to: https://github.com/${REPO_NAME}/settings/secrets/actions"
    echo ""
    echo "Add these secrets:"
    echo ""
    echo "1. DO_HOST"
    echo "   Value: $DO_HOST"
    echo ""
    echo "2. DO_USER"
    echo "   Value: $DO_USER"
    echo ""
    echo "3. DO_SSH_KEY"
    echo "   Value: (copy the entire content below)"
    echo "   ──────────────────────────────────────"
    cat "$SSH_KEY_PATH"
    echo "   ──────────────────────────────────────"
    echo ""
    echo "⚠️  Make sure to copy the ENTIRE key including -----BEGIN and -----END lines"
fi

# Step 5: Verify secrets (if using CLI)
if [ "$USE_GH_CLI" = true ]; then
    echo ""
    echo "🔍 Verifying secrets..."
    if gh secret list --repo "$REPO_NAME" | grep -q "DO_HOST"; then
        echo "✅ Secrets verified in GitHub"
    else
        echo "⚠️  Could not verify secrets. Please check manually."
    fi
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Push to master branch to trigger deployment"
echo "2. Check Actions tab: https://github.com/${REPO_NAME}/actions"
echo "3. Watch the deployment workflow run"
echo ""
echo "Your SSH key is stored at: $SSH_KEY_PATH"
echo "Keep this key secure - it provides access to your droplet!"

