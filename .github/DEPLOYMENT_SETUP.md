# GitHub Actions Deployment Setup

This repository uses GitHub Actions to automatically deploy to Digital Ocean when code is pushed to the `master` branch.

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository:

1. Go to: **Settings → Secrets and variables → Actions → New repository secret**

2. Add these secrets:

### `DO_HOST`
- **Value**: Your Digital Ocean droplet IP address
- **Example**: `159.65.18.16`

### `DO_USER`
- **Value**: SSH username (usually `root` for Digital Ocean)
- **Example**: `root`

### `DO_SSH_KEY`
- **Value**: Your private SSH key for accessing the droplet
- **How to get it**:
  ```bash
  # On your local machine, if you don't have a key pair:
  ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/do_deploy
  
  # Copy the public key to your droplet:
  ssh-copy-id -i ~/.ssh/do_deploy.pub root@your-droplet-ip
  
  # Copy the private key content:
  cat ~/.ssh/do_deploy
  # Copy the entire output (including -----BEGIN and -----END lines)
  ```

## How It Works

1. **On Push to Master**:
   - Runs all tests (backend + frontend)
   - If tests pass, deploys to Digital Ocean
   - Builds Docker images
   - Runs migrations
   - Restarts services

2. **On Pull Requests**:
   - Only runs tests (no deployment)

3. **Manual Trigger**:
   - You can manually trigger deployment from Actions tab

## Deployment Process

The deployment workflow:
1. ✅ Runs backend tests (pytest)
2. ✅ Runs frontend tests (vitest)
3. ✅ SSH into Digital Ocean droplet
4. ✅ Pulls latest code from master branch
5. ✅ Builds Docker images
6. ✅ Starts/restarts containers
7. ✅ Runs database migrations
8. ✅ Collects static files

## Troubleshooting

### Deployment fails with SSH error
- Check that `DO_SSH_KEY` secret is correctly set (include BEGIN/END lines)
- Verify `DO_HOST` and `DO_USER` are correct
- Test SSH connection manually: `ssh -i ~/.ssh/do_deploy root@your-droplet-ip`

### Tests fail in CI
- Check test logs in GitHub Actions
- Ensure all dependencies are in `requirements.txt` and `package.json`
- Run tests locally first: `pytest` and `npm test`

### Deployment succeeds but site is down
- Check Docker containers: `docker-compose -f docker-compose.prod.yml ps`
- Check logs: `docker-compose -f docker-compose.prod.yml logs`
- Verify `.env.prod` file exists on server

