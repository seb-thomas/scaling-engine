# Quick Setup Guide for GitHub Secrets

## Step 1: Generate SSH Key for Deployment

Run these commands on your local machine:

```bash
# Generate a new SSH key pair for GitHub Actions
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/do_deploy -N ""

# Copy the public key to your Digital Ocean droplet
ssh-copy-id -i ~/.ssh/do_deploy.pub root@159.65.18.16

# Display the private key (you'll copy this to GitHub)
cat ~/.ssh/do_deploy
```

## Step 2: Add Secrets to GitHub

### Option A: Using GitHub CLI (Fastest)

```bash
# Install gh CLI if needed: brew install gh
# Login: gh auth login

# Add the secrets
gh secret set DO_HOST --body "159.65.18.16"
gh secret set DO_USER --body "root"

# For SSH key, copy the entire output from: cat ~/.ssh/do_deploy
gh secret set DO_SSH_KEY < ~/.ssh/do_deploy
```

### Option B: Using GitHub Web UI

1. Go to: https://github.com/seb-thomas/scaling-engine/settings/secrets/actions
2. Click "New repository secret" for each:

   **DO_HOST**
   - Name: `DO_HOST`
   - Value: `159.65.18.16`

   **DO_USER**
   - Name: `DO_USER`
   - Value: `root`

   **DO_SSH_KEY**
   - Name: `DO_SSH_KEY`
   - Value: (paste entire content of `~/.ssh/do_deploy`, including `-----BEGIN` and `-----END` lines)

## Step 3: Verify Setup

After adding secrets, you can test by:
1. Making a small change and pushing to master
2. Check Actions tab: https://github.com/seb-thomas/scaling-engine/actions
3. Watch the deployment workflow run

## Troubleshooting

If deployment fails:
- Check Actions logs for specific errors
- Verify SSH key was copied correctly (include BEGIN/END lines)
- Test SSH manually: `ssh -i ~/.ssh/do_deploy root@159.65.18.16`
- Ensure droplet has Docker and docker-compose installed

