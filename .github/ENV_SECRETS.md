# Environment Variables and Secrets Management

This project uses GitHub Secrets to securely manage sensitive environment variables for production deployment.

## Sensitive Variables (GitHub Secrets)

The following variables are stored as GitHub Secrets and should **never** be committed to the repository:

- `SECRET_KEY` - Django secret key (required)
- `SQL_PASSWORD` - PostgreSQL database password (required)
- `ANTHROPIC_API_KEY` - Claude API key for AI book extraction (optional)

## Non-Sensitive Variables (in .env.prod.example)

These variables are safe to commit and are stored in `.env.prod.example`:

- `DEBUG` - Django debug mode (0 for production)
- `DJANGO_ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `SQL_ENGINE` - Database engine (django.db.backends.postgresql)
- `SQL_DATABASE` - Database name (paperwaves_prod)
- `SQL_USER` - Database user (paperwaves_user)
- `SQL_HOST` - Database host (db)
- `SQL_PORT` - Database port (5432)
- `CELERY_BROKER_URL` - Redis broker URL
- `CELERY_RESULT_BACKEND` - Redis result backend URL
- `BOOK_EXTRACTION_MODE` - Book extraction mode (ai, keyword, or both)

## Setting Up Secrets

### Option 1: Using GitHub CLI (Recommended)

```bash
# Make the script executable
chmod +x setup-env-secrets.sh

# Run the setup script
./setup-env-secrets.sh
```

The script will:
- Read current values from `.env.prod` (if it exists)
- Prompt you to use or generate new values
- Set the secrets in GitHub

### Option 2: Using GitHub Web UI

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:
   - Name: `SECRET_KEY`, Value: (your Django secret key)
   - Name: `SQL_PASSWORD`, Value: (your database password)
   - Name: `ANTHROPIC_API_KEY`, Value: (your Claude API key, optional)

### Option 3: Using GitHub CLI Manually

```bash
# Set SECRET_KEY
echo "your-secret-key-here" | gh secret set SECRET_KEY

# Set SQL_PASSWORD
echo "your-db-password-here" | gh secret set SQL_PASSWORD

# Set ANTHROPIC_API_KEY (optional)
echo "your-api-key-here" | gh secret set ANTHROPIC_API_KEY
```

## How Deployment Works

The GitHub Actions deployment workflow (`deploy.yml`) automatically:

1. **Reads secrets** from GitHub Secrets
2. **Generates `.env.prod`** on the server with all environment variables
3. **Generates `.env.prod.db`** with database configuration
4. **Uses these files** in Docker Compose

The `.env.prod` file is generated on the server during deployment and is never committed to the repository.

## Local Development

For local development, create your own `.env.prod` and `.env.prod.db` files:

```bash
# Copy the example file
cp .env.prod.example .env.prod

# Edit with your local values
nano .env.prod
```

**Important**: Add `.env.prod*` to `.gitignore` (already done) to prevent committing sensitive values.

## Updating Secrets

To update a secret:

```bash
# Using GitHub CLI
echo "new-value" | gh secret set SECRET_NAME

# Or use the setup script again
./setup-env-secrets.sh
```

## Viewing Secrets

You can view secret names (but not values) using:

```bash
gh secret list
```

Secret values are encrypted and cannot be retrieved once set. If you need to update a secret but don't remember the current value, you'll need to set a new one.

## Security Best Practices

1. ✅ **Do**: Use GitHub Secrets for sensitive values
2. ✅ **Do**: Keep `.env.prod` in `.gitignore`
3. ✅ **Do**: Use strong, randomly generated passwords
4. ❌ **Don't**: Commit `.env.prod` or `.env.prod.db` to the repository
5. ❌ **Don't**: Share secrets in chat, email, or documentation
6. ❌ **Don't**: Use the same secrets across different environments

