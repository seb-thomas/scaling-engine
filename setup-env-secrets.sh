#!/bin/bash

# Script to set up GitHub Secrets for environment variables
# This helps manage sensitive values securely instead of keeping them in .env files

set -e

echo "🔐 Setting up GitHub Secrets for environment variables"
echo ""
echo "This script will help you add sensitive environment variables to GitHub Secrets."
echo "These secrets will be used during deployment to generate .env files on the server."
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "   Install it from: https://cli.github.com/"
    echo "   Or use the GitHub web UI to add secrets manually."
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI."
    echo "   Run: gh auth login"
    exit 1
fi

echo "📋 The following secrets will be set:"
echo "   - SECRET_KEY (Django secret key)"
echo "   - SQL_PASSWORD (PostgreSQL password)"
echo "   - ANTHROPIC_API_KEY (Claude API key, optional)"
echo ""

# Read current values from .env.prod if it exists
if [ -f .env.prod ]; then
    echo "📖 Reading values from .env.prod..."
    CURRENT_SECRET_KEY=$(grep "^SECRET_KEY=" .env.prod | cut -d '=' -f2- | tr -d '"')
    CURRENT_SQL_PASSWORD=$(grep "^SQL_PASSWORD=" .env.prod | cut -d '=' -f2- | tr -d '"')
    CURRENT_ANTHROPIC_KEY=$(grep "^ANTHROPIC_API_KEY=" .env.prod | cut -d '=' -f2- | tr -d '"' || echo "")
    
    if [ -n "$CURRENT_SECRET_KEY" ] && [ "$CURRENT_SECRET_KEY" != "change-me-to-a-secure-random-string" ]; then
        echo "   Found SECRET_KEY in .env.prod"
        read -p "   Use this value? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            CURRENT_SECRET_KEY=""
        fi
    else
        CURRENT_SECRET_KEY=""
    fi
    
    if [ -n "$CURRENT_SQL_PASSWORD" ] && [ "$CURRENT_SQL_PASSWORD" != "change-me-to-a-secure-password" ]; then
        echo "   Found SQL_PASSWORD in .env.prod"
        read -p "   Use this value? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            CURRENT_SQL_PASSWORD=""
        fi
    else
        CURRENT_SQL_PASSWORD=""
    fi
    
    if [ -n "$CURRENT_ANTHROPIC_KEY" ]; then
        echo "   Found ANTHROPIC_API_KEY in .env.prod"
        read -p "   Use this value? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            CURRENT_ANTHROPIC_KEY=""
        fi
    fi
fi

# Get SECRET_KEY
if [ -z "$CURRENT_SECRET_KEY" ]; then
    echo ""
    echo "Enter Django SECRET_KEY (or press Enter to generate one):"
    read -r SECRET_KEY
    if [ -z "$SECRET_KEY" ]; then
        SECRET_KEY=$(openssl rand -hex 50)
        echo "   Generated: ${SECRET_KEY:0:20}..."
    fi
else
    SECRET_KEY="$CURRENT_SECRET_KEY"
fi

# Get SQL_PASSWORD
if [ -z "$CURRENT_SQL_PASSWORD" ]; then
    echo ""
    echo "Enter SQL_PASSWORD (or press Enter to generate one):"
    read -r SQL_PASSWORD
    if [ -z "$SQL_PASSWORD" ]; then
        SQL_PASSWORD=$(openssl rand -hex 20)
        echo "   Generated: ${SQL_PASSWORD:0:20}..."
    fi
else
    SQL_PASSWORD="$CURRENT_SQL_PASSWORD"
fi

# Get ANTHROPIC_API_KEY (optional)
if [ -z "$CURRENT_ANTHROPIC_KEY" ]; then
    echo ""
    echo "Enter ANTHROPIC_API_KEY (optional, press Enter to skip):"
    read -r ANTHROPIC_API_KEY
else
    ANTHROPIC_API_KEY="$CURRENT_ANTHROPIC_KEY"
fi

echo ""
echo "🚀 Setting GitHub Secrets..."

# Set secrets
echo "$SECRET_KEY" | gh secret set SECRET_KEY
echo "   ✅ SECRET_KEY set"

echo "$SQL_PASSWORD" | gh secret set SQL_PASSWORD
echo "   ✅ SQL_PASSWORD set"

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "$ANTHROPIC_API_KEY" | gh secret set ANTHROPIC_API_KEY
    echo "   ✅ ANTHROPIC_API_KEY set"
else
    echo "   ⏭️  ANTHROPIC_API_KEY skipped (optional)"
fi

echo ""
echo "✅ All secrets have been set!"
echo ""
echo "📝 Next steps:"
echo "   1. The deployment workflow will automatically use these secrets"
echo "   2. Update your local .env.prod if needed (it won't be committed)"
echo "   3. The server will generate .env.prod from secrets during deployment"
echo ""
echo "💡 To view secrets (names only): gh secret list"
echo "💡 To delete a secret: gh secret delete SECRET_NAME"

